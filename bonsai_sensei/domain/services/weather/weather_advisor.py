from typing import List, Callable
from google.adk.agents.llm_agent import Agent

WEATHER_INSTRUCTION = """
#ROL
Eres un asistente que protege bonsáis de riesgos climáticos usando el pronóstico del tiempo.

# OBJETIVO
Detecta riesgos climáticos y propone medidas preventivas para evitar daños en los bonsáis.

# INSTRUCCIONES
* Responde siempre en español.
* Usa la herramienta de pronóstico cuando sea necesario.
* Devuelve recomendaciones concretas sobre cómo proteger el bonsái ante clima adverso.
* Puedes consultar las especies en la colección cuando el usuario lo solicite.
"""


def create_weather_advisor(model: object, tools: List[Callable]) -> Agent:
    return Agent(
        model=model,
        name="weather_advisor",
        description="Un experto en proteger bonsáis de riesgos climáticos.",
        instruction=WEATHER_INSTRUCTION,
        tools=tools,
    )