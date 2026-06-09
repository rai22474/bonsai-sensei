import uuid
from typing import Callable

from google.adk.agents.llm_agent import Agent
from google.adk.runners import InMemoryRunner, RunConfig
from google.genai import types

from bonsai_sensei.domain.services.extract_text_from_events import extract_text_from_events

_APP_NAME = "photo_comparison"
_MAX_LLM_CALLS = 5

_COMPARISON_INSTRUCTION = """
Eres el kantei de bonsáis, experto en comparación visual de árboles a lo largo del tiempo.

Recibirás dos fotos del mismo bonsái tomadas en momentos distintos y una intención de comparación.
Describe los cambios observables entre ambas fotos orientándote a esa intención.
Indica claramente qué ha cambiado, en qué dirección y qué aspectos permanecen iguales.
Sé preciso y útil, no genérico.

Responde en castellano.
Usa Markdown: **negrita**, *cursiva*, listas con - y saltos de línea.
"""


def create_photo_comparison_runner(model: object) -> Callable:
    async def run_photo_comparison(
        photo_bytes_older: bytes,
        photo_bytes_newer: bytes,
        comparison_intent: str,
    ) -> str:
        agent = Agent(
            model=model,
            name=_APP_NAME,
            instruction=_COMPARISON_INSTRUCTION,
        )
        runner = InMemoryRunner(agent=agent, app_name=_APP_NAME)
        session_id = str(uuid.uuid4())
        await runner.session_service.create_session(
            app_name=_APP_NAME,
            user_id=_APP_NAME,
            session_id=session_id,
        )
        message = types.Content(
            role="user",
            parts=[
                types.Part(inline_data=types.Blob(mime_type="image/webp", data=photo_bytes_older)),
                types.Part(inline_data=types.Blob(mime_type="image/webp", data=photo_bytes_newer)),
                types.Part(text=comparison_intent or "Describe los cambios observables entre ambas fotos."),
            ],
        )
        return await extract_text_from_events(runner.run_async(
            user_id=_APP_NAME,
            session_id=session_id,
            new_message=message,
            run_config=RunConfig(max_llm_calls=_MAX_LLM_CALLS),
        ))

    return run_photo_comparison
