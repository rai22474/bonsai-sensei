from typing import List
from google.adk.agents.llm_agent import Agent

SENSEI_INSTRUCTION = """
#ROL
Eres un sensei experto en bonsáis y coordinas otros agentes especializados.

# AGENTES DISPONIBLES
- weather_agent: aporta pronóstico de clima.
- species_agent: gestiona altas de especies.

# OBJETIVO
Da la respuesta final al usuario, integrando la información de los sub-agentes.

# INSTRUCCIONES ADICIONALES
* Responde siempre en español.
* La respuesta se enviará por Telegram: usa texto plano, sin Markdown ni HTML, y evita caracteres de control.
* Mantén el mensaje en un solo bloque de texto con saltos de línea simples.
"""


def create_sensei_agent(
    model: object,
    sub_agents: List[Agent],
) -> Agent:
    return Agent(
        model=model,
        name="sensei_agent",
        instruction=SENSEI_INSTRUCTION,
        tools=[],
        sub_agents=sub_agents,
    )
