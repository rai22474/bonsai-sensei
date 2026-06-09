from typing import Callable

from google.genai import types

from bonsai_sensei.domain.services.extract_text_from_events import extract_text_from_events
from bonsai_sensei.domain.services.llm_runner import create_single_turn_llm_runner

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
    run_llm = create_single_turn_llm_runner(
        model=model,
        app_name=_APP_NAME,
        instruction=_COMPARISON_INSTRUCTION,
        max_llm_calls=_MAX_LLM_CALLS,
    )

    async def run_photo_comparison(
        photo_bytes_older: bytes,
        photo_bytes_newer: bytes,
        comparison_intent: str,
    ) -> str:
        message = types.Content(
            role="user",
            parts=[
                types.Part(inline_data=types.Blob(mime_type="image/webp", data=photo_bytes_older)),
                types.Part(inline_data=types.Blob(mime_type="image/webp", data=photo_bytes_newer)),
                types.Part(text=comparison_intent or "Describe los cambios observables entre ambas fotos."),
            ],
        )
        return await extract_text_from_events(run_llm(message))

    return run_photo_comparison
