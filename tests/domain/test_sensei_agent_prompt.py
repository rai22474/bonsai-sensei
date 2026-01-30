import os
from typing import AsyncGenerator, Callable, List

import pytest
import pytest_asyncio
from hamcrest import all_of, assert_that, contains_string
from dotenv import load_dotenv
from strands.agent import Agent
from strands.models.model import Model
from strands.types.streaming import StreamEvent

from bonsai_sensei.domain.services.strands_helpers import agent_text
from bonsai_sensei.domain.services.bonsai.bonsai_agent import BONSAI_INSTRUCTION
from bonsai_sensei.domain.services.sensei import create_sensei
from bonsai_sensei.domain.services.species.botanist import SPECIES_INSTRUCTION
from bonsai_sensei.domain.services.weather.weather_advisor import WEATHER_INSTRUCTION
from bonsai_sensei.model_factory import get_model_factory


load_dotenv()


@pytest.mark.integration
@pytest.mark.asyncio
async def should_return_sensei_response_with_bonsai_summary(fake_advisor):
    fake_advisor.bonsai_llm.when_call().then("Bonsáis registrados:\n- Olmo 1 (Olmo)")

    result = await fake_advisor.run("Lista mis bonsáis")

    assert_that(
        result["response"],
        all_of(
            contains_string("Bonsáis registrados"),
            contains_string("Olmo 1 (Olmo)"),
        ),
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def should_return_care_guide_for_bonsai(fake_advisor):
    fake_advisor.bonsai_llm.when_call().then(
        "Bonsái: Olmo 1. Especie: Olmo (Ulmus parvifolia)."
    )
    (
        fake_advisor.species_llm.when("Ulmus parvifolia")
        .then("GUÍA_OLMO: Riego moderado, luz indirecta y poda en primavera.")
        .or_else("No puedo dar la guía sin una especie confirmada.")
    )
    result = await fake_advisor.run(
        "Dame la guía de cultivo de bonsai de mi colección que se llama Olmo 1"
    )

    assert_that(result["response"], contains_string("GUÍA_OLMO"))


@pytest.mark.integration
@pytest.mark.asyncio
async def should_not_return_care_guide_without_species(fake_advisor):
    fake_advisor.bonsai_llm.when_call().then("Bonsái: Olmo 1. Especie: desconocida.")
    (
        fake_advisor.species_llm.when("Ulmus parvifolia")
        .then("GUÍA_OLMO: Riego moderado, luz indirecta y poda en primavera.")
        .or_else("No puedo dar la guía sin una especie confirmada.")
    )

    result = await fake_advisor.run("Dame la guía de cultivo del Olmo 1")

    assert_that(result["response"], contains_string("sin una especie"))


@pytest_asyncio.fixture
async def fake_advisor():
    os.environ.setdefault("LLM_TARGET", llm_target)
    sensei_llm = get_model_factory()()

    bonsai_llm = ScriptedModel(
        model="bonsai-fake",
        responses=[],
    )
    weather_llm = ScriptedModel(model="weather-fake", responses=[])
    species_llm = ScriptedModel(
        model="species-fake",
        responses=[],
    )

    bonsai_agent = Agent(
        model=bonsai_llm,
        name="bonsai_agent",
        system_prompt=BONSAI_INSTRUCTION,
    )
    
    weather_agent = Agent(
        model=weather_llm,
        name="weather_agent",
        system_prompt=WEATHER_INSTRUCTION,
    )
    species_agent = Agent(
        model=species_llm,
        name="species_agent",
        system_prompt=SPECIES_INSTRUCTION,
    )

    llm_target = os.getenv("LLM_TARGET", "local").lower()
    if llm_target == "cloud" and not os.getenv("GEMINI_API_KEY"):
        os.environ.setdefault("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", ""))
    if llm_target == "cloud":
        os.environ.setdefault("GEMINI_MODEL", "gemini-2.0-flash")
    if llm_target == "local":
        os.environ.setdefault("OLLAMA_API_BASE", "http://localhost:11434")

    sensei_agent = create_sensei(
        model=sensei_llm,
        sub_agents=[bonsai_agent, species_agent, weather_agent],
    )

    return FakeAdvisor(sensei_agent, bonsai_llm, species_llm)


class ScriptedModel(Model):
    def __init__(self, model: str, responses: List[str]):
        self._model = model
        self._responses = list(responses)
        self._calls = 0
        self._conditional_responses = []

    def update_config(self, **model_config) -> None:
        self._config = model_config

    def get_config(self) -> dict:
        return {"model_id": self._model}

    async def structured_output(
        self, output_model, prompt, system_prompt: str | None = None, **kwargs
    ) -> AsyncGenerator[dict, None]:
        text = _next_scripted_text(prompt, self._conditional_responses, self._responses)
        try:
            output = output_model.model_validate_json(text)
        except Exception:
            output = output_model.model_validate({})
        yield {"structured_output": output}

    async def stream(
        self,
        messages,
        tool_specs=None,
        system_prompt: str | None = None,
        **kwargs,
    ) -> AsyncGenerator[StreamEvent, None]:
        self._calls += 1
        text = _next_scripted_text(
            messages, self._conditional_responses, self._responses
        )
        yield {"messageStart": {"role": "assistant"}}
        yield {"contentBlockStart": {"contentBlockIndex": 0, "start": {}}}
        yield {"contentBlockDelta": {"contentBlockIndex": 0, "delta": {"text": text}}}
        yield {"contentBlockStop": {"contentBlockIndex": 0}}
        yield {"messageStop": {"stopReason": "end_turn"}}

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


def _messages_text(messages) -> str:
    texts = []
    for message in messages or []:
        for block in message.get("content", []):
            if isinstance(block, dict) and "text" in block:
                text = block.get("text")
                if text:
                    texts.append(text)
    return " ".join(texts)


class ScriptedModelRule:
    def __init__(self, model: ScriptedModel, text: str):
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
    text = request if isinstance(request, str) else _messages_text(request)
    for predicate, queued in conditional_responses:
        if queued and predicate(text):
            return queued.pop(0)
    if responses:
        return responses.pop(0)
    return "OK"


class FakeAdvisor:
    def __init__(
        self,
        sensei_agent: Agent,
        bonsai_llm: ScriptedModel,
        species_llm: ScriptedModel,
    ):
        self.bonsai_llm = bonsai_llm
        self.species_llm = species_llm
        self.sensei_agent = sensei_agent

    async def run(self, text: str) -> dict:
        result = await self.sensei_agent.invoke_async(text)
        response = agent_text(result)
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
