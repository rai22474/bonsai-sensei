from google.adk.agents.llm_agent import LlmAgent
from bonsai_sensei.domain.services.single_tool_call_callback import limit_to_single_tool_call

SEKO_INSTRUCTION = """
Eres el ejecutor de trabajos de cultivo de bonsáis. Recibes un plan de acción y lo ejecutas paso a paso.

# Contexto
{cultivation_plan}

# Comportamiento
Ejecuta cada paso en el orden indicado usando las herramientas y agentes disponibles.
Si un paso falla, incluye el error en el resultado junto con los pasos ya completados.

Devuelve los resultados en JSON:
{{
  "goal": "<objetivo del plan>",
  "results": [
    {{"order": 1, "action": "<nombre>", "result": "<resultado>"}},
    ...
  ]
}}
"""


def create_seko(model: object, tools: list) -> LlmAgent:
    return LlmAgent(
        model=model,
        name="seko",
        description="Ejecutor del plan de trabajos de cultivo usando herramientas y agentes especializados.",
        instruction=SEKO_INSTRUCTION,
        after_model_callback=limit_to_single_tool_call,
        tools=tools,
        output_key="cultivation_execution_result",
    )
