from google.adk.agents.llm_agent import Agent
from google.adk.tools import AgentTool

CULTIVATION_INSTRUCTION = """
# ROL
Eres un experto en cultivo de bonsáis que coordina especialistas en cada
una de las áreas clave para el cultivo.

# OBJETIVO
Se encarga de cualquier consulta relacionada con el cuidado de bonsáis,
coordinando las respuestas de los agentes especialistas:
- Especies y cuidados específicos: delega al botanist.
- Condiciones climáticas: delega al weather_advisor.
- Plan de trabajos (fertilizaciones, trasplantes, tratamientos, colección del usuario): delega al planning_agent.

# REGLA DE DELEGACIÓN
* Para cualquier solicitud relacionada con el plan de trabajos (planificar, ver, consultar el fin de semana),
  delega DIRECTAMENTE al planning_agent. No consultes al botanist ni al weather_advisor antes.
"""


def create_cultivation_agent(
    model: object,
    botanist: Agent,
    weather_advisor: Agent,
    planning_agent: Agent,
) -> Agent:
    return Agent(
        model=model,
        name="cultivation_agent",
        description="Coordina especies, clima y plan de trabajos para el cuidado de bonsáis. Crea y gestiona trabajos planificados (fertilizaciones, trasplantes, tratamientos fitosanitarios futuros).",
        instruction=CULTIVATION_INSTRUCTION,
        tools=[
            AgentTool(botanist),
            AgentTool(weather_advisor),
            AgentTool(planning_agent),
        ],
    )
