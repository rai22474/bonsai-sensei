from pathlib import Path

from google.adk.agents.llm_agent import LlmAgent
from google.adk.planners import BuiltInPlanner
from google.genai.types import ThinkingConfig
from jinja2 import Environment, FileSystemLoader

_TEMPLATE_DIR = Path(__file__).parent / "templates"


def create_mitori(model: object, agent_descriptions: list[str]) -> LlmAgent:
    env = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)), trim_blocks=True, lstrip_blocks=True)
    instruction = env.get_template("mitori_instruction.j2").render(
        available_agents="\n".join(agent_descriptions)
    )
    return LlmAgent(
        model=model,
        name="mitori",
        description="Estratega que analiza la petición y genera un plan de acción revisado en JSON.",
        instruction=instruction,
        output_key="action_plan",
        planner=BuiltInPlanner(thinking_config=ThinkingConfig(include_thoughts=False)),
    )
