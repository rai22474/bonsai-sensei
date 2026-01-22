from typing import List, Callable
from functools import partial
from google.adk.agents.llm_agent import Agent
from google.adk.runners import InMemoryRunner
from bonsai_sensei.logging_config import get_logger
from dotenv import load_dotenv

load_dotenv()

logger = get_logger(__name__)

SENSEI_INSTRUCTION = """
#ROL
Eres un asistente útil especializado en el cuidado de bonsáis. 

# OBJETIVO
Tu objetivo es proporcionar consejos precisos y prácticos para el cuidado de bonsáis, 
teniendo en cuenta factores como la especie del bonsái, las condiciones climáticas y las mejores prácticas de jardinería.

# INSTRUCCIONES ADICIONALES
* Responde siempre en español.
* La respuesta se enviará por Telegram: usa texto plano, sin Markdown ni HTML, y evita caracteres de control.
* Mantén el mensaje en un solo bloque de texto con saltos de línea simples.
"""

def create_sensei(tools: List[Callable], model_factory: Callable[[], object]) -> InMemoryRunner | None:
    model = model_factory()
    agent = Agent(
        model=model,
        name="weather_agent",
        instruction=SENSEI_INSTRUCTION,
        tools=tools,
    )

    return partial(
        _generate_advise,
        runner=InMemoryRunner(agent=agent, app_name="bonsai_sensei"),
    )


async def _generate_advise(
    text: str, runner: InMemoryRunner, user_id: str = "default_user"
) -> str:
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
