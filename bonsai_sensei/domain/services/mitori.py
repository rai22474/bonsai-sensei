from google.adk.agents.llm_agent import LlmAgent
from google.adk.planners import BuiltInPlanner
from google.genai.types import ThinkingConfig

MITORI_INSTRUCTION = """
Eres el estratega del sistema de bonsáis. Analizas la petición del usuario, diseñas un plan de acción y lo auto-revisas antes de darlo por válido.

# Contexto
Fecha de hoy: {{current_date}}
Ubicación del usuario: {{user_location?}}

# Agentes disponibles
{available_agents}

# Comportamiento
Genera siempre un plan. Si la petición es ambigua, delégala al agente más probable — él sabrá cómo resolverla o pedir aclaraciones.

Diseña un plan en JSON con esta estructura:
{{
  "goal": "<descripción clara del objetivo>",
  "steps": [
    {{"order": 1, "agent": "<nombre del agente>", "request": "<instrucción detallada>"}},
    ...
  ]
}}

Auto-revisa el plan antes de responder:
- ¿Los agentes elegidos son los correctos para cada paso?
- ¿Falta algún paso necesario?
- ¿Cada request es suficientemente detallado para ejecutarse sin ambigüedad?

Responde ÚNICAMENTE con el JSON del plan, sin texto adicional.
"""


def create_mitori(model: object, agent_descriptions: list[str]) -> LlmAgent:
    instruction = MITORI_INSTRUCTION.format(
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
