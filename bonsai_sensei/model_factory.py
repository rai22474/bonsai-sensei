import os
from google.adk.models.lite_llm import LiteLlm


def get_local_model_factory():
    def factory():
        model_name = os.getenv("OLLAMA_MODEL", "qwen3:32b")
        api_base = os.getenv("OLLAMA_API_BASE", "http://host.docker.internal:11434")
        os.environ["OLLAMA_API_BASE"] = api_base
        return LiteLlm(model=f"ollama_chat/{model_name}")

    return factory


def get_cloud_model_factory():
    def factory():
        return os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")

    return factory
