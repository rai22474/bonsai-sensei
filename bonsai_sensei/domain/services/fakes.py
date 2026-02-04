import os
from typing import Callable, Dict, List


FAKE_SERVICES_ENV = "USE_FAKE_SERVICES"


def use_fake_services() -> bool:
    return os.getenv(FAKE_SERVICES_ENV, "").lower() in {"1", "true", "yes"}


def create_fake_tavily_searcher() -> Callable[[str], Dict]:
    def search(query: str) -> Dict:
        return {
            "answer": "Aplicar 10 ml/L cada 15 días. Uso recomendado para bonsáis.",
            "results": [
                {"url": "https://example.com/fake-source-1"},
                {"url": "https://example.com/fake-source-2"},
            ],
        }

    return search


def fake_trefle_search(common_name: str) -> List[Dict[str, str]]:
    return [{"scientific_name": "Juniperus procumbens"}]


def fake_translate_to_english(common_name: str) -> str:
    return "Juniperus procumbens"


async def fake_weather(location: str) -> str:
    return (
        "Weather in Madrid: Current: Clear, 2°C. Min/Max: 0°C/5°C. "
        "Max Frost Chance: 80%. WARNING: High risk of frost (80%). "
        "Hourly: 00:00h: 1°C, Frost chance: 80%; 03:00h: 0°C, "
        "Frost chance: 75%; 06:00h: 1°C, Frost chance: 60%"
    )
