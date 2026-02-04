import os

from deepeval.metrics import GEval
from deepeval.models import OllamaModel
from deepeval.test_case import LLMTestCaseParams


def create_judge_model():
    model_name = os.getenv("OLLAMA_JUDGE_MODEL") or os.getenv(
        "OLLAMA_MODEL", "qwen2.5:32b-instruct"
    )
    base_url = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
    return OllamaModel(model=model_name, base_url=base_url)


def create_recommendation_metric(name: str, criteria: str):
    return GEval(
        name=name,
        criteria=criteria,
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
        ],
        model=create_judge_model(),
        threshold=0.5,
        async_mode=False,
    )
