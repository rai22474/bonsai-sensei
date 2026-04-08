from typing import List
from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools import AgentTool

SHOKUNIN_INSTRUCTION = """
#ROL
Eres el ejecutor del sistema de bonsáis. Recibes un plan de acción y lo ejecutas paso a paso.

# PLAN DE ACCIÓN
{action_plan}

# OBJETIVO
Ejecutar el plan usando los agentes especializados disponibles y devolver los resultados.

# INSTRUCCIONES
* Lee el plan del campo "action_plan" del contexto.
* Ejecuta cada paso en el orden indicado delegando al agente correspondiente con el request especificado.
* Si un agente devuelve un resultado con "confirmation_pending", detén la ejecución inmediatamente e incluye ese resultado — NO intentes confirmar ni llamar al agente de nuevo. La confirmación la hará el usuario.
* Si un paso falla, incluye el error en el resultado junto con los pasos ya completados.
* Devuelve un JSON con los resultados de cada paso:
  {{
    "goal": "<objetivo del plan>",
    "results": [
      {{"order": 1, "agent": "<nombre>", "result": "<resultado del paso>"}},
      ...
    ]
  }}
"""


def create_shokunin(model: object, tools: List[AgentTool]) -> LlmAgent:
    return LlmAgent(
        model=model,
        name="shokunin",
        description="Ejecutor que implementa el plan de acción usando los agentes especializados.",
        instruction=SHOKUNIN_INSTRUCTION,
        tools=tools,
        output_key="execution_result",
    )
