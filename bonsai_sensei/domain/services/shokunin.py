from typing import List
from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools import AgentTool

SHOKUNIN_INSTRUCTION = """
Eres el ejecutor del sistema de bonsáis. Recibes un plan de acción y lo ejecutas paso a paso.

# Contexto
{action_plan}

# Comportamiento
Ejecuta cada paso en el orden indicado delegando al agente indicado. Para cada paso, pasa al agente la intención completa junto con todos los parámetros concretos que el usuario proporcionó, sin omitir ni reformular valores.
Si un paso indica que el usuario ha cancelado la operación: detén la ejecución y devuelve el resultado con status "cancelled". No ejecutes pasos adicionales.
Si un paso falla por error técnico: incluye el error en el resultado junto con los pasos ya completados.

Devuelve un JSON con los resultados:
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
