from typing import Callable

from google.adk.agents.llm_agent import Agent
from google.adk.tools import AgentTool

PLANNING_INSTRUCTION = """
# ROL
Eres un experto en planificación de trabajos de cultivo de bonsáis. Te encargas de gestionar
el plan de trabajos futuros: fertilizaciones, trasplantes y tratamientos fitosanitarios.

# DISPONIBILIDAD Y FIN DE SEMANA
* El usuario tiene más tiempo para cuidar los bonsáis durante el fin de semana (sábados y domingos).
* Cuando el usuario solicite planificar un trabajo sin especificar fecha, propón el próximo sábado
  como fecha por defecto. Usa get_current_date si necesitas saber la fecha actual.
* Si el usuario pregunta qué tiene planificado para el fin de semana, usa list_weekend_planned_works
  para obtener todos los trabajos del próximo sábado y domingo de un vistazo.

# PLANES DE TRABAJO
* Si el usuario quiere ver el plan de trabajos de un bonsái concreto:
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

# COLECCIÓN
* Si necesitas saber qué bonsáis hay en la colección (por ejemplo, para planificar o responder
  preguntas generales sobre todos los bonsáis), usa list_bonsai para obtener la lista completa.

# REPLANIFICACIÓN
* Si el usuario pide revisar o replanificar los trabajos de un bonsái:
    1. Usa list_planned_works_for_bonsai para ver el plan actual (incluye los ids de cada trabajo).
    2. Usa list_bonsai_events_for_cultivation para ver el historial de eventos recientes.
    3. Determina qué trabajos ya no son válidos (ya realizados, sin sentido dado el historial, etc.).
    4. Usa confirm_delete_planned_work para eliminar cada trabajo obsoleto (necesitas su id).
    5. Usa confirm_create_planned_work si el plan necesita nuevos trabajos actualizados.
* Si el usuario pide directamente eliminar un trabajo planificado concreto,
  usa confirm_delete_planned_work con su id.
* Una vez registrada la confirmación de borrado, NO vuelvas a llamar a confirm_delete_planned_work.
"""


def create_planning_agent(
    model: object,
    fertilizer_advisor: Agent,
    phytosanitary_advisor: Agent,
    list_planned_works_tool: Callable | None = None,
    list_bonsai_events_tool: Callable | None = None,
    confirm_create_planned_work_tool: Callable | None = None,
    confirm_delete_planned_work_tool: Callable | None = None,
    list_collection_tool: Callable | None = None,
    list_weekend_planned_works_tool: Callable | None = None,
) -> Agent:
    direct_tools = [
        tool
        for tool in [
            list_planned_works_tool,
            list_bonsai_events_tool,
            confirm_create_planned_work_tool,
            confirm_delete_planned_work_tool,
            list_collection_tool,
            list_weekend_planned_works_tool,
        ]
        if tool is not None
    ]
    return Agent(
        model=model,
        name="planning_agent",
        description="Gestiona el plan de trabajos de cultivo: crea, lista y consulta fertilizaciones, trasplantes y tratamientos fitosanitarios planificados para los bonsáis.",
        instruction=PLANNING_INSTRUCTION,
        tools=[
            AgentTool(fertilizer_advisor),
            AgentTool(phytosanitary_advisor),
            *direct_tools,
        ],
    )
