import os
from typing import AsyncGenerator, Callable, Iterable, List

import pytest
import pytest_asyncio
from deepeval import assert_test
from deepeval.metrics import PatternMatchMetric
from deepeval.test_case import LLMTestCase
from dotenv import load_dotenv
from google.adk.agents.llm_agent import Agent
from google.adk.models import base_llm
from google.adk.tools import AgentTool
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types

from bonsai_sensei.domain.services.advisor import create_advisor
from bonsai_sensei.domain.services.bonsai.gardener import GARDENER_INSTRUCTION
from bonsai_sensei.domain.services.sensei import create_sensei
from bonsai_sensei.domain.services.cultivation.species.botanist import SPECIES_INSTRUCTION
from bonsai_sensei.domain.services.cultivation.weather.weather_advisor import WEATHER_INSTRUCTION
from bonsai_sensei.model_factory import get_cloud_model_factory, get_local_model_factory


load_dotenv()


@pytest.mark.integration
@pytest.mark.asyncio
async def should_return_sensei_response_with_bonsai_summary(fake_advisor):
    fake_advisor.gardener_llm.when_call().then("Bonsáis registrados:\n- Olmo 1 (Ulmus parvifolia)")

    result = await fake_advisor.run("Lista mis bonsáis")

    _assert_matches_pattern(
        prompt="Lista mis bonsáis",
        response=result["response"],
        pattern=r"(?s).*Olmo 1.*(Ulmus parvifolia|Olmo).*",
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def should_return_care_guide_for_bonsai(fake_advisor):
    fake_advisor.gardener_llm.when_call().then(
        "Bonsái: Frieren. Especie: Olmo (Ulmus parvifolia)."
    )
    (
        fake_advisor.species_llm.when("Ulmus parvifolia")
        .then("GUÍA_OLMO: Riego moderado, luz indirecta y poda en primavera.")
        .or_else("No puedo dar la guía sin una especie confirmada.")
    )
    result = await fake_advisor.run(
        "Dame la guía de cultivo de bonsai de mi colección que se llama Frieren"
    )

    _assert_matches_pattern(
        prompt="Dame la guía de cultivo de bonsai de mi colección que se llama Frieren",
        response=result["response"],
        pattern=r"(?s).*(riego moderado|luz indirecta|poda en primavera).*",
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def should_not_return_care_guide_without_species(fake_advisor):
    fake_advisor.gardener_llm.when_call().then("Bonsái: Fern. Especie: desconocida.")
    (
        fake_advisor.species_llm.when("Ulmus parvifolia")
        .then("GUÍA_OLMO: Riego moderado, luz indirecta y poda en primavera.")
        .or_else("No puedo dar la guía sin una especie confirmada.")
    )

    result = await fake_advisor.run("Dame la guía de cultivo de Fern")

    _assert_matches_pattern(
        prompt="Dame la guía de cultivo de Fern",
        response=result["response"],
        pattern=(
            r"(?s).*(sin una especie|especie.*desconocida|no puedo|"
            r"no tengo la información|no puede.*proporcionar).*"
        ),
    )


@pytest_asyncio.fixture
async def fake_advisor():
    target = os.getenv("LLM_TARGET", "local").lower()
    model_factory = (
        get_local_model_factory() if target == "local" else get_cloud_model_factory()
    )
    sensei_llm = model_factory()

    gardener_llm = ScriptedLlm(model="gardener-fake", responses=[])
    weather_llm = ScriptedLlm(model="weather-fake", responses=[])
    species_llm = ScriptedLlm(model="species-fake", responses=[])

    gardener_agent = Agent(
        model=gardener_llm,
        name="gardener",
        instruction=GARDENER_INSTRUCTION,
    )

    weather_agent = Agent(
        model=weather_llm,
        name="weather_advisor",
        instruction=WEATHER_INSTRUCTION,
    )
    species_agent = Agent(
        model=species_llm,
        name="botanist",
        instruction=SPECIES_INSTRUCTION,
    )

    sensei_tools = [
        AgentTool(gardener_agent),
        AgentTool(species_agent),
        AgentTool(weather_agent),
    ]
    sensei_agent = create_sensei(
        model=sensei_llm,
        tools=sensei_tools,
    )
    advisor = create_advisor(sensei_agent, trace_handler=_trace_fake_advisor)
    return FakeAdvisor(advisor, gardener_llm, species_llm)


class ScriptedLlm(base_llm.BaseLlm):
    model: str

    def __init__(self, model: str, responses: List[str]):
        super().__init__(model=model)
        self._responses = list(responses)
        self._calls = 0
        self._conditional_responses = []

    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False
    ) -> AsyncGenerator[LlmResponse, None]:
        self._calls += 1
        text = _next_scripted_text(
            _contents_text(llm_request.contents),
            self._conditional_responses,
            self._responses,
        )
        yield LlmResponse(
            content=types.Content(role="model", parts=[types.Part(text=text)]),
            partial=False,
        )

    @property
    def calls(self) -> int:
        return self._calls

    def set_responses(self, responses: List[str]) -> None:
        self._responses = list(responses)

    def set_conditional_responses(
        self,
        predicate: Callable[[str], bool],
        responses: List[str],
    ) -> None:
        self._conditional_responses = [(predicate, list(responses))]

    def when(self, text: str) -> "ScriptedModelRule":
        return ScriptedModelRule(self, text)

    def when_call(self) -> "ScriptedModelRule":
        return ScriptedModelRule(self, "")


def _contents_text(contents) -> str:
    texts = []
    for content in contents or []:
        for part in getattr(content, "parts", []) or []:
            if part.text:
                texts.append(part.text)
    return " ".join(texts)


def _assert_matches_pattern(prompt: str, response: str, pattern: str) -> None:
    test_case = LLMTestCase(input=prompt, actual_output=response)
    metric = PatternMatchMetric(pattern=pattern, ignore_case=True)
    assert_test(test_case=test_case, metrics=[metric], run_async=False)


class ScriptedModelRule:
    def __init__(self, model: ScriptedLlm, text: str):
        self.model = model
        self.text = text

    def then(self, response: str) -> "ScriptedModelRule":
        if self.text:
            self.model.set_conditional_responses(
                lambda request: self.text in request,
                [response],
            )
        else:
            self.model.set_responses([response])
        return self

    def or_else(self, response: str) -> None:
        self.model.set_responses([response])


def _next_scripted_text(
    request,
    conditional_responses: List[tuple[Callable[[str], bool], List[str]]],
    responses: List[str],
) -> str:
    text = request if isinstance(request, str) else _contents_text(request)
    for predicate, queued in conditional_responses:
        if queued and predicate(text):
            return queued.pop(0)
    if responses:
        return responses.pop(0)
    return "OK"


def _trace_fake_advisor(_: str, events: list) -> None:
    for event in events:
        _trace_agent_event(event)


def _trace_agent_event(event) -> None:
    agent_name = _first_attr(event, ["agent_name", "agent", "name", "author", "sender"])
    input_value = _first_attr(
        event, ["input", "inputs", "request", "user_messages", "prompt"]
    )
    output_text = _extract_event_text(event)
    tool_calls = _extract_tool_calls(event)
    tool_responses = _extract_tool_responses(event)
    input_text = _normalize_text_value(input_value)
    agent_label = str(agent_name) if agent_name else "unknown_agent"
    if input_text or output_text:
        print(
            f"agent_trace agent={agent_label} input={input_text} output={output_text}"
        )
    for tool_call in tool_calls:
        print(
            f"tool_trace agent={agent_label} tool={tool_call['name']} args={tool_call['args']}"
        )
    for tool_response in tool_responses:
        print(
            f"tool_trace agent={agent_label} tool={tool_response['name']} output={tool_response['output']}"
        )


def _extract_event_text(event) -> str:
    content = getattr(event, "content", None)
    if not content:
        return ""
    parts = getattr(content, "parts", None) or []
    texts = [part.text for part in parts if getattr(part, "text", None)]
    return " ".join(texts).strip()


def _first_attr(source: object, names: Iterable[str]):
    for name in names:
        value = getattr(source, name, None)
        if value:
            return value
    return None


def _normalize_text_value(value) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    return str(value)


def _extract_tool_calls(event) -> list[dict]:
    content = getattr(event, "content", None)
    if not content:
        return []
    parts = getattr(content, "parts", None) or []
    calls = []
    for part in parts:
        call = getattr(part, "function_call", None)
        if not call:
            continue
        name = getattr(call, "name", None) or getattr(call, "function_name", None)
        args = getattr(call, "args", None) or getattr(call, "arguments", None)
        calls.append(
            {
                "name": _normalize_text_value(name) or "unknown_tool",
                "args": _normalize_text_value(args),
            }
        )
    return calls


def _extract_tool_responses(event) -> list[dict]:
    content = getattr(event, "content", None)
    if not content:
        return []
    parts = getattr(content, "parts", None) or []
    responses = []
    for part in parts:
        response = getattr(part, "function_response", None)
        if not response:
            continue
        name = getattr(response, "name", None) or getattr(
            response, "function_name", None
        )
        output = (
            getattr(response, "response", None)
            or getattr(response, "result", None)
            or getattr(response, "output", None)
        )
        responses.append(
            {
                "name": _normalize_text_value(name) or "unknown_tool",
                "output": _normalize_text_value(output),
            }
        )
    return responses


class FakeAdvisor:
    def __init__(
        self,
        advisor: Callable[..., str],
        gardener_llm: ScriptedLlm,
        species_llm: ScriptedLlm,
    ):
        self.gardener_llm = gardener_llm
        self.species_llm = species_llm
        self._advisor = advisor

    async def run(self, text: str) -> dict:
        response = await self._advisor(text)
        log_lines = [
            f"input={text}",
            f"response={response}",
        ]
        for line in log_lines:
            print(line)
        return {
            "response": response,
            "log_lines": log_lines,
        }
