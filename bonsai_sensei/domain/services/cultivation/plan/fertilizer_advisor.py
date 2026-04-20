from google.adk.agents.llm_agent import Agent

FERTILIZER_ADVISOR_INSTRUCTION = """
Eres un experto en fertilizantes para bonsáis. Ayudas a seleccionar el fertilizante adecuado para planificar fertilizaciones futuras.

# Comportamiento
Consulta el catálogo con list_fertilizers_for_planning y el historial del bonsái con list_bonsai_events_for_cultivation.
Recomienda el fertilizante más adecuado en función de la disponibilidad y el historial.
"""


def create_fertilizer_advisor(model: object, tools: list) -> Agent:
    return Agent(
        model=model,
        name="fertilizer_advisor",
        description="""Experto en fertilizantes disponibles e historial de fertilizaciones. 
        Recomienda qué fertilizante usar para planificar fertilizaciones futuras.""",
        instruction=FERTILIZER_ADVISOR_INSTRUCTION,
        tools=tools,
    )
