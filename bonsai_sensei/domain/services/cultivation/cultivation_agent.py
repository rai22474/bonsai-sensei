from typing import Callable

from google.adk.agents.llm_agent import Agent
from google.adk.tools import AgentTool

CULTIVATION_INSTRUCTION = """
#ROL
Eres un experto en cultivo de bonsáis que coordina especialistas en cada
una de las áreas clave para el cultivo.

# OBJETIVO
Se encarga de cualquier consulta relacionada con el cuidado de bonsáis,
coordinando las respuestas de los agentes especialistas.

Tiene especial conocimiento en las siguientes áreas:
- Especies de bonsáis y sus cuidados específicos.
- Condiciones climáticas ideales para el cultivo de bonsáis.
- Plan de trabajos de cultivo para cada bonsái.

# PLANES DE TRABAJO
* Si el usuario quiere ver el plan de trabajos de un bonsái:
    - Usa list_planned_works_for_bonsai para obtener los trabajos planificados.
    - Presenta los trabajos ordenados por fecha de forma legible.
* Si el usuario quiere planificar una fertilización:
    - Si no especifica el fertilizante, delega al fertilizer_advisor para que
      consulte los fertilizantes disponibles y el historial del bonsái y recomiende uno.
    - Recoge bonsai_name, fertilizer_name, amount y scheduled_date.
    - Usa work_type="fertilizer_application" al llamar a confirm_create_planned_work.
* Si el usuario quiere planificar un tratamiento fitosanitario:
    - Si no especifica el producto, delega al phytosanitary_advisor para que
      consulte los productos disponibles y el historial del bonsái y recomiende uno.
    - Recoge bonsai_name, phytosanitary_name, amount y scheduled_date.
    - Usa work_type="phytosanitary_application" al llamar a confirm_create_planned_work.
* Si el usuario quiere planificar un trasplante:
    - Recoge pot_size, pot_type y substrate si los conoces.
    - Usa work_type="transplant" al llamar a confirm_create_planned_work.
* Una vez registrada la confirmación, NO vuelvas a llamar a confirm_create_planned_work.
"""


def create_cultivation_agent(
    model: object,
    botanist: Agent,
    weather_advisor: Agent,
    fertilizer_advisor: Agent,
    phytosanitary_advisor: Agent,
    list_planned_works_tool: Callable | None = None,
    confirm_create_planned_work_tool: Callable | None = None,
) -> Agent:
    direct_tools = [
        tool
        for tool in [list_planned_works_tool, confirm_create_planned_work_tool]
        if tool is not None
    ]
    return Agent(
        model=model,
        name="cultivation_agent",
        description="Coordina especies, clima y plan de trabajos para el cuidado de bonsáis. Crea y gestiona trabajos planificados (fertilizaciones, trasplantes, tratamientos fitosanitarios futuros).",
        instruction=CULTIVATION_INSTRUCTION,
        tools=[
            AgentTool(botanist),
            AgentTool(weather_advisor),
            AgentTool(fertilizer_advisor),
            AgentTool(phytosanitary_advisor),
            *direct_tools,
        ],
    )
