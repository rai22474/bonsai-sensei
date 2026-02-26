from google.adk.agents.llm_agent import Agent

FERTILIZER_ADVISOR_INSTRUCTION = """
# ROL
Eres un experto en fertilizantes para bonsáis. Ayudas al experto en cultivo a
seleccionar el fertilizante adecuado para planificar fertilizaciones futuras.

# OBJETIVO
- Cuando se te pida sugerencias de fertilizante, usa list_fertilizers_for_planning
  para obtener los fertilizantes disponibles en el catálogo.
- Cuando se necesite consultar el historial de fertilizaciones de un bonsái,
  usa list_bonsai_events_for_cultivation para recuperar sus eventos registrados.
- Recomienda el fertilizante más adecuado en función de la disponibilidad y el historial.
"""


def create_fertilizer_advisor(model: object, tools: list) -> Agent:
    return Agent(
        model=model,
        name="fertilizer_advisor",
        description="Experto en fertilizantes disponibles e historial de fertilizaciones. Recomienda qué fertilizante usar para planificar fertilizaciones futuras.",
        instruction=FERTILIZER_ADVISOR_INSTRUCTION,
        tools=tools,
    )
