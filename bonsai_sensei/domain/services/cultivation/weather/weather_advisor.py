from typing import List, Callable
from google.adk.agents.llm_agent import Agent

WEATHER_INSTRUCTION = """
#ROL
Eres un asistente que protege bonsáis de riesgos climáticos usando el pronóstico del tiempo.

# OBJETIVO
Detecta riesgos climáticos y propone medidas preventivas para evitar daños en los bonsáis.

# INSTRUCCIONES
* Responde siempre en español.
* Si el usuario no indica su ubicación en el mensaje, usa la herramienta get_user_location para obtener su ubicación registrada antes de consultar el tiempo. No preguntes al usuario por su ubicación.
* Usa la herramienta de pronóstico cuando sea necesario.
* Si no hay riesgo climático, indica claramente que no hace falta protección y evita recomendar medidas preventivas.
* Si hay clima adverso, devuelve recomendaciones concretas sobre cómo proteger el bonsái.
* Puedes consultar las especies en la colección cuando el usuario lo solicite.
"""


def create_weather_advisor(model: object, tools: List[Callable]) -> Agent:
    return Agent(
        model=model,
        name="weather_advisor",
        description="Consulta el pronóstico del tiempo y evalúa riesgos climáticos (heladas, calor extremo) para bonsáis. Úsalo únicamente cuando el usuario pregunta explícitamente por el tiempo o necesita saber si sus bonsáis están en riesgo climático. No lo uses para decidir fechas de planificación.",
        instruction=WEATHER_INSTRUCTION,
        tools=tools,
    )
