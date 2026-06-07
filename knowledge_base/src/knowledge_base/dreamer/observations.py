import functools
import json
import re
import uuid
from pathlib import Path
from typing import Callable

from google.adk.agents.invocation_context import LlmCallsLimitExceededError
from google.adk.agents.llm_agent import Agent
from google.adk.runners import InMemoryRunner, RunConfig
from google.genai import types
from jinja2 import Environment, FileSystemLoader

from knowledge_base.logging_config import get_logger
from knowledge_base.wiki_page_tools import create_read_wiki_page_tool, create_write_wiki_page_tool

logger = get_logger(__name__)

_TEMPLATE_DIR = Path(__file__).parent / "templates"
_MAX_CLASSIFY_CALLS = 3
_MAX_ENRICH_CALLS = 10

_REQUIRES_USER_ID = {"bonsai", "profile"}
_ENTITY_TYPES = {"species", "techniques", "diseases", "pests"}


async def execute_integrate_observations(
    observations: list[dict],
    classify_observation: Callable,
    enrich_wiki_page: Callable,
    read_wiki_page_func: Callable,
    write_wiki_page_func: Callable,
) -> None:
    for obs in observations:
        content = obs.get("content", "")
        user_id = obs.get("user_id")
        if not content:
            continue
        try:
            classification = await classify_observation(content, user_id)
        except Exception:
            logger.warning("Failed to classify observation, skipping")
            continue
        if not classification:
            continue
        wiki_path = _build_observation_path(
            classification.get("type"),
            classification.get("entity_name", ""),
            user_id,
        )
        if not wiki_path:
            logger.debug("No wiki path for type=%s entity=%s, skipping", classification.get("type"), classification.get("entity_name"))
            continue
        existing_page = read_wiki_page_func(path=wiki_path)
        existing_content = existing_page.get("content", "") if isinstance(existing_page, dict) and existing_page.get("status") == "success" else ""
        try:
            enriched = await enrich_wiki_page(wiki_path, existing_content, content)
        except Exception:
            logger.warning("Failed to enrich wiki page %s, skipping", wiki_path)
            continue
        if enriched:
            write_wiki_page_func(path=wiki_path, content=enriched)
            logger.info("Integrated observation into %s", wiki_path)


def _build_observation_path(obs_type: str | None, entity_name: str, user_id: str | None) -> str | None:
    """Route observation to wiki path based on type and user_id.

    User observations (user_id set) always go to user zone.
    Admin corrections (user_id=None) go to global wiki.
    """
    if not obs_type or obs_type == "ignore":
        return None
    slug = re.sub(r"[^a-z0-9]+", "-", entity_name.lower()).strip("-") if entity_name else ""
    if obs_type in _REQUIRES_USER_ID and not user_id:
        return None
    if user_id is not None:
        match obs_type:
            case "bonsai":
                return f"users/{user_id}/bonsai/{slug}/index.md" if slug else None
            case "species" | "techniques" | "diseases" | "pests":
                return f"users/{user_id}/{obs_type}-notes/{slug}.md" if slug else None
            case "profile":
                return f"users/{user_id}/profile/preferences.md"
            case _:
                return None
    else:
        match obs_type:
            case "species" | "techniques" | "diseases" | "pests":
                return f"{obs_type}/{slug}.md" if slug else None
            case _:
                return None


def create_observations_runner(model, wiki_root: Path) -> Callable:
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    classify_instruction = env.get_template("observation_classify.j2").render()
    classify_prompt_template = env.get_template("observation_classify_prompt.j2")
    enrich_instruction = env.get_template("observation_enrich.j2").render()
    enrich_prompt_template = env.get_template("observation_enrich_prompt.j2")

    classify_agent = Agent(model=model, name="obs_classifier", instruction=classify_instruction)
    enrich_agent = Agent(model=model, name="obs_enricher", instruction=enrich_instruction)

    return functools.partial(
        execute_integrate_observations,
        classify_observation=_create_classify_func(classify_agent, classify_prompt_template),
        enrich_wiki_page=_create_enrich_func(enrich_agent, enrich_prompt_template),
        read_wiki_page_func=create_read_wiki_page_tool(str(wiki_root)),
        write_wiki_page_func=create_write_wiki_page_tool(wiki_root),
    )


def _create_classify_func(agent: Agent, prompt_template) -> Callable:
    async def classify_observation(content: str, user_id: str | None) -> dict | None:
        prompt = prompt_template.render(content=content, user_id=user_id)
        text = await _run_llm_for_text(agent, prompt, _MAX_CLASSIFY_CALLS)
        if not text:
            return None
        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1]).strip()
        try:
            return json.loads(cleaned)
        except (json.JSONDecodeError, ValueError):
            logger.warning("Failed to parse classification JSON: %s", cleaned[:200])
            return None
    return classify_observation


def _create_enrich_func(agent: Agent, prompt_template) -> Callable:
    async def enrich_wiki_page(path: str, existing_content: str, observation: str) -> str | None:
        prompt = prompt_template.render(path=path, existing_content=existing_content, observation=observation)
        return await _run_llm_for_text(agent, prompt, _MAX_ENRICH_CALLS)
    return enrich_wiki_page


async def _run_llm_for_text(agent: Agent, prompt: str, max_llm_calls: int) -> str | None:
    runner = InMemoryRunner(agent=agent, app_name=agent.name)
    session_id = str(uuid.uuid4())
    await runner.session_service.create_session(
        app_name=agent.name, user_id=agent.name, session_id=session_id
    )
    message = types.Content(role="user", parts=[types.Part(text=prompt)])
    last_text = None
    try:
        async for event in runner.run_async(
            user_id=agent.name,
            session_id=session_id,
            new_message=message,
            run_config=RunConfig(max_llm_calls=max_llm_calls),
        ):
            if hasattr(event, "content") and event.content:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        last_text = part.text
    except LlmCallsLimitExceededError:
        logger.warning("LLM calls limit reached for agent %s", agent.name)
    return last_text
