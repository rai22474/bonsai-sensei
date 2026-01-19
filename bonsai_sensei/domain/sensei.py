from functools import partial
import os
from google.adk.agents.llm_agent import Agent
from google.adk.tools.openapi_tool import OpenAPIToolset

from google.adk.tools.openapi_tool.auth.auth_helpers import token_to_scheme_credential

from google.adk.runners import InMemoryRunner
from bonsai_sensei.logging_config import get_logger
from bonsai_sensei.domain.weather_tool import get_weather
from bonsai_sensei.domain.garden_tool import get_garden_species
from dotenv import load_dotenv

load_dotenv()


logger = get_logger(__name__)


SENSEI_INSTRUCTION = """
#ROL
Eres un asistente útil especializado en el cuidado de bonsáis. 

# OBJETIVO
Tu objetivo es proporcionar consejos precisos y prácticos para el cuidado de bonsáis, 
teniendo en cuenta factores como la especie del bonsái, las condiciones climáticas y las mejores prácticas de jardinería.

# HERRAMIENTAS
* get_weather para encontrar información meteorológica cuando sea necesario para contestar correctamente a la pregunta. 
* get_garden_species para conocer qué árboles tiene el usuario en su jardín, sus edades y especies.

# INSTRUCCIONES ADICIONALES
* Responde siempre en español.
"""


def create_sensei() -> InMemoryRunner | None:

    agent = Agent(
        model="gemini-3-flash-preview",
        name="weather_agent",
        instruction=SENSEI_INSTRUCTION,
        tools=[get_weather, get_garden_species],
    )

    return partial(
        _generate_advise,
        runner=InMemoryRunner(agent=agent, app_name="bonsai_sensei"),
    )


async def _generate_advise(
    text: str, runner: InMemoryRunner, user_id: str = "default_user"
) -> str:
    """
    Processes a user message to generate advice about bonsai care using the Google Agent Development Kit (ADK).
    """
    if not runner:
        return "No puedo procesar tu solicitud porque el agente no está inicializado (probablemente falta la API Key)."

    logger.info(f"Processing message from {user_id}: {text}")

    events = await runner.run_debug(
        user_messages=text,
        user_id=user_id,
        session_id=str(user_id),
        quiet=True,
    )

    response_texts = _compose_response(events)

    if not response_texts:
        return "Pensando... (No se recibió respuesta de texto)"

    return "\n".join(response_texts)


def _compose_response(events):
    response_texts = []
    for event in events:
        if event.author == "weather_agent" and event.content:
            if hasattr(event.content, "parts") and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        response_texts.append(part.text)

    return response_texts
