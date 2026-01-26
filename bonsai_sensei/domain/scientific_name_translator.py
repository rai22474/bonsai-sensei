from deep_translator import GoogleTranslator
from deep_translator.exceptions import TranslationNotFound, NotValidPayload, RequestError


def translate_to_english(common_name: str) -> str:
    try:
        return GoogleTranslator(source="auto", target="en").translate(common_name)
    except (TranslationNotFound, NotValidPayload, RequestError):
        return ""
