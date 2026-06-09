import uuid
from pathlib import Path
from typing import Callable

from google.adk.agents.llm_agent import Agent
from google.adk.memory import BaseMemoryService
from google.adk.runners import InMemoryRunner, Runner, RunConfig
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService
from google.genai import types
from jinja2 import Environment, FileSystemLoader

from bonsai_sensei.domain.services.extract_text_from_events import extract_text_from_events

_APP_NAME = "mimamori"
_MAX_LLM_CALLS = 20
_TEMPLATE_DIR = Path(__file__).parent / "templates"


def create_mimamori_agent_runner(
    model: object,
    search_wiki_knowledge: Callable | None = None,
    read_wiki_page: Callable | None = None,
    list_bonsai_events: Callable | None = None,
    memory_service: BaseMemoryService | None = None,
) -> Callable:
    env = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)), trim_blocks=True, lstrip_blocks=True)
    instruction = env.get_template("mimamori_instruction.j2").render()
    tools = [tool for tool in [search_wiki_knowledge, read_wiki_page, list_bonsai_events] if tool is not None]

    async def run_mimamori_reflection(prompt: str, user_id: str) -> str:
        agent = Agent(model=model, name=_APP_NAME, instruction=instruction, tools=tools)
        if memory_service is not None:
            runner = Runner(
                app_name=_APP_NAME,
                agent=agent,
                artifact_service=InMemoryArtifactService(),
                session_service=InMemorySessionService(),
                memory_service=memory_service,
            )
        else:
            runner = InMemoryRunner(agent=agent, app_name=_APP_NAME)
        session_id = str(uuid.uuid4())
        await runner.session_service.create_session(
            app_name=_APP_NAME,
            user_id=user_id,
            session_id=session_id,
        )
        return await extract_text_from_events(runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=types.Content(role="user", parts=[types.Part(text=prompt)]),
            run_config=RunConfig(max_llm_calls=_MAX_LLM_CALLS),
        ))

    return run_mimamori_reflection
