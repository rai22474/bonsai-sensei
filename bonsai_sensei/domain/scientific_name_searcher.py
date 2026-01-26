from typing import List, Dict
import os
from urllib.parse import quote
import httpx
from bonsai_sensei.logging_config import get_logger

logger = get_logger(__name__)


def trefle_search(common_name: str) -> List[Dict[str, str]]:
    api_token = os.getenv("TREFLE_API_TOKEN")
    if not api_token:
        raise ValueError("Trefle API token is required")

    query = quote(common_name)
    url = f"https://trefle.io/api/v1/plants/search?q={query}&token={api_token}"
    logger.info("Trefle search: %s", common_name)
    try:
        response = httpx.get(url, timeout=20.0)
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError:
        logger.info("Trefle search failed")
        return []
    logger.info("Trefle results count: %s", len(payload.get("data", [])))
    return payload.get("data", [])
