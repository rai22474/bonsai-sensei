from google.adk.agents.llm_agent import Agent
from google.adk.tools import AgentTool

CULTIVATION_INSTRUCTION = """
#ROL
Eres un experto en cultivo de bonsáis que coordina especialistas en cada
una de las áreas clave para el cultivo.

# OBJETIVO
Se encarga de cualquier consulta relacionada con el cuidado de bonsáis,
coordinando las respuestas de los agentes especialistas.
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
