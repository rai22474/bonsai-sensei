import logging
import os

import litellm

from deepeval.metrics import GEval
from deepeval.models import LiteLLMModel
from deepeval.test_case import LLMTestCaseParams

logger = logging.getLogger(__name__)
litellm.drop_params = True


def create_judge_model():
    model, base_url = resolve_judge_config()
    logger.info(
        "Judge model configured: %s (base_url=%s)",
        model,
        base_url,
    )
    return LiteLLMModel(
        model=model,
        base_url=base_url,
        drop_params=True, 
        temperature=1.0
    )


def resolve_judge_config() -> tuple[str, str | None]:
    model = os.getenv("JUDGE_MODEL", "ollama/qwen2.5:32b-instruct")
    
    base_url = os.getenv("JUDGE_BASE_URL")
    if base_url is None and model.startswith("ollama/"):
        base_url = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
    
    return model, base_url


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
