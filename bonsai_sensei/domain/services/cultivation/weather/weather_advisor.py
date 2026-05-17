from typing import List, Callable
from google.adk.agents.llm_agent import Agent

WEATHER_INSTRUCTION = """
Eres un asistente que protege bonsáis de riesgos climáticos usando el pronóstico del tiempo.

# Comportamiento
Si la ubicación del usuario no está disponible, obtenla antes de consultar el tiempo. No preguntes al usuario por su ubicación.
Si no hay riesgo climático, indícalo claramente sin proponer medidas preventivas.
Si hay clima adverso, devuelve recomendaciones concretas sobre cómo proteger el bonsái.

# Formato
Responde en castellano.
Usa HTML compatible con Telegram: <b>negrita</b>, <i>cursiva</i>, listas con • y saltos de línea. No uses Markdown.
"""


def create_weather_advisor(model: object, tools: List[Callable]) -> Agent:
    return Agent(
        model=model,
        name="weather_advisor",
        description="Consulta el pronóstico del tiempo y evalúa riesgos climáticos (heladas, calor extremo) para bonsáis. Úsalo únicamente cuando el usuario pregunta explícitamente por el tiempo o necesita saber si sus bonsáis están en riesgo climático. No lo uses para decidir fechas de planificación.",
        instruction=WEATHER_INSTRUCTION,
        tools=tools,
    )
