from google.adk.agents.llm_agent import Agent

PHYTOSANITARY_ADVISOR_INSTRUCTION = """
# ROL
Eres un experto en productos fitosanitarios para bonsáis. Ayudas al experto en cultivo a
seleccionar el tratamiento adecuado para planificar tratamientos fitosanitarios futuros.

# OBJETIVO
- Cuando se te pida sugerencias de producto fitosanitario, usa list_phytosanitary_for_planning
  para obtener los productos disponibles en el catálogo.
- Cuando se necesite consultar el historial de tratamientos de un bonsái,
  usa list_bonsai_events_for_cultivation para recuperar sus eventos registrados.
- Recomienda el producto más adecuado en función de la disponibilidad y el historial.
"""


def create_phytosanitary_advisor(model: object, tools: list) -> Agent:
    return Agent(
        model=model,
        name="phytosanitary_advisor",
        description="Experto en productos fitosanitarios disponibles e historial de tratamientos. Recomienda qué producto usar para planificar tratamientos fitosanitarios futuros.",
        instruction=PHYTOSANITARY_ADVISOR_INSTRUCTION,
        tools=tools,
    )
