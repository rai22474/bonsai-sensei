import os
import time

from google.adk.models.google_llm import Gemini

from knowledge_base.metrics import LLM_REQUEST_DURATION, LLM_REQUESTS_TOTAL, LLM_TOKENS_TOTAL


class InstrumentedGemini(Gemini):
    async def generate_content_async(self, llm_request, stream=False):
        start = time.perf_counter()
        model_name = self.model or "unknown"
        status = "success"
        last_response = None
        try:
            async for response in super().generate_content_async(llm_request, stream):
                last_response = response
                yield response
        except Exception:
            status = "error"
            raise
        finally:
            LLM_REQUEST_DURATION.labels(model=model_name).observe(time.perf_counter() - start)
            LLM_REQUESTS_TOTAL.labels(model=model_name, status=status).inc()
            if last_response and last_response.usage_metadata:
                usage = last_response.usage_metadata
                if usage.prompt_token_count:
                    LLM_TOKENS_TOTAL.labels(model=model_name, token_type="input").inc(usage.prompt_token_count)
                if usage.candidates_token_count:
                    LLM_TOKENS_TOTAL.labels(model=model_name, token_type="output").inc(usage.candidates_token_count)


def get_local_model_factory():
    def factory():
        from google.adk.models.lite_llm import LiteLlm
        model_name = os.getenv("OLLAMA_MODEL", "qwen2.5:32b-instruct")
        api_base = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
        os.environ["OLLAMA_API_BASE"] = api_base
        return LiteLlm(model=f"ollama_chat/{model_name}")

    return factory


def get_cloud_model_factory():
    def factory():
        model_name = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
        return InstrumentedGemini(model=model_name)

    return factory


def get_cloud_orchestrator_model_factory():
    def factory():
        model_name = os.getenv("GEMINI_ORCHESTRATOR_MODEL", "gemini-3-flash-preview")
        return InstrumentedGemini(model=model_name) if model_name else None

    return factory
