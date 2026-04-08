from google.adk.agents.llm_agent import LlmAgent

SEKO_INSTRUCTION = """
#ROL
Eres el ejecutor de trabajos de cultivo de bonsáis. Recibes un plan de acción y lo ejecutas paso a paso.

# PLAN DE ACCIÓN
{cultivation_plan}

# INSTRUCCIONES
* Ejecuta cada paso en el orden indicado usando las herramientas y agentes disponibles.
* Si un agente o herramienta devuelve un resultado con "confirmation_pending", detén la ejecución e incluye ese resultado — NO llames de nuevo a esa herramienta ni intentes confirmar. La confirmación la hará el usuario.
* Si un paso usa fertilizer_advisor o phytosanitary_advisor, úsalos como agentes y pasa su resultado al siguiente paso.
* Si un paso falla, incluye el error en el resultado junto con los pasos ya completados.
* Devuelve los resultados en JSON:
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
        tools=tools,
        output_key="cultivation_execution_result",
    )
