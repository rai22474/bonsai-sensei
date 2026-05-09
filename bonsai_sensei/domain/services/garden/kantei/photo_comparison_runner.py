import uuid
from typing import Callable

from google.adk.agents.llm_agent import Agent
from google.adk.runners import InMemoryRunner, RunConfig
from google.genai import types

_APP_NAME = "photo_comparison"
_MAX_LLM_CALLS = 5

_COMPARISON_INSTRUCTION = """
Eres el kantei de bonsáis, experto en comparación visual de árboles a lo largo del tiempo.

Recibirás dos fotos del mismo bonsái tomadas en momentos distintos y una intención de comparación.
Describe los cambios observables entre ambas fotos orientándote a esa intención.
Indica claramente qué ha cambiado, en qué dirección y qué aspectos permanecen iguales.
Sé preciso y útil, no genérico.

Responde en castellano.
Usa HTML compatible con Telegram: <b>negrita</b>, <i>cursiva</i>, listas con • y saltos de línea.
No uses Markdown.
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
        run_config = RunConfig(max_llm_calls=_MAX_LLM_CALLS)
        response_parts = []
        async for event in runner.run_async(
            user_id=_APP_NAME,
            session_id=session_id,
            new_message=message,
            run_config=run_config,
        ):
            if event.content and hasattr(event.content, "parts"):
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        response_parts.append(part.text)
        return "\n".join(response_parts)

    return run_photo_comparison
