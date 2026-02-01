from google.adk.agents.llm_agent import Agent
from google.adk.tools import AgentTool

CULTIVATION_INSTRUCTION = """
#ROL
Eres cultivation_agent y coordinas especialistas en especies y clima para bonsáis.

# OBJETIVO
Resolver preguntas sobre especies y pronóstico del tiempo para el cuidado de bonsáis.

# INSTRUCCIONES
* Usa botanist para especies, guías de cultivo y gestión de especies.
* Usa weather_advisor para pronósticos y recomendaciones climáticas.
* Devuelve la respuesta literal del agente especialista.
* Responde siempre en español.
"""


def create_cultivation_agent(
    model: object,
    botanist: Agent,
    weather_advisor: Agent,
) -> Agent:
    return Agent(
        model=model,
        name="cultivation_agent",
        description="Coordina especies y clima para el cuidado de bonsáis.",
        instruction=CULTIVATION_INSTRUCTION,
        tools=[
            AgentTool(botanist),
            AgentTool(weather_advisor),
        ],
    )
