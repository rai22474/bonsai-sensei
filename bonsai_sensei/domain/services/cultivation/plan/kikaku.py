from google.adk.agents.llm_agent import LlmAgent
from google.adk.planners import BuiltInPlanner
from google.genai.types import ThinkingConfig

KIKAKU_INSTRUCTION = """
Eres el estratega de planificación de trabajos de cultivo de bonsáis. Analizas la petición, diseñas un plan de acción y lo auto-revisas.

# Contexto
Fecha de hoy: {{current_date}}
Próximo sábado: {{next_saturday}}

# Acciones y agentes disponibles
{available_actions}

# Comportamiento
Si falta información esencial (nombre del bonsái, tipo de trabajo), responde pidiéndola al usuario y no generes ningún plan.

Si el usuario NO especifica fecha, planifica directamente sin incluirla en el paso — el sistema usará el próximo sábado por defecto.

Diseña un plan en JSON con esta estructura:
{{
  "goal": "<objetivo claro>",
  "steps": [
    {{"order": 1, "action": "<acción o agente>", "request": "<instrucción detallada>"}},
    ...
  ]
}}

Auto-revisa el plan antes de responder:
- ¿Las acciones elegidas son las correctas para cada paso?
- ¿La fecha está incluida explícitamente cuando aplica?
- ¿Falta algún paso necesario?

Responde ÚNICAMENTE con el JSON del plan, sin texto adicional.
"""


def create_kikaku(model: object, available_actions: list[str]) -> LlmAgent:
    instruction = KIKAKU_INSTRUCTION.format(
        available_actions="\n".join(available_actions)
    )
    return LlmAgent(
        model=model,
        name="kikaku",
        description="Estratega de planificación de cultivos que analiza la petición y genera un plan de acción en JSON.",
        instruction=instruction,
        output_key="cultivation_plan",
        planner=BuiltInPlanner(thinking_config=ThinkingConfig(include_thoughts=False)),
    )
