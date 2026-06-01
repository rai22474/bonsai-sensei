import concurrent.futures
import os

from deep_translator import GoogleTranslator
from deep_translator.exceptions import TranslationNotFound, NotValidPayload, RequestError

_TRANSLATION_TIMEOUT_SECONDS = 10.0


def translate_to_english(common_name: str) -> str:
    if os.getenv("GOOGLE_TRANSLATE_ENABLED", "true").lower() == "false":
        return ""
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        translation_future = executor.submit(
            GoogleTranslator(source="auto", target="en").translate,
            common_name,
        )
        try:
            return translation_future.result(timeout=_TRANSLATION_TIMEOUT_SECONDS)
        except (concurrent.futures.TimeoutError, TranslationNotFound, NotValidPayload, RequestError):
            return ""
