from typing import Callable, List, Dict
import os
from urllib.parse import quote
import httpx
from bonsai_sensei.logging_config import get_logger

logger = get_logger(__name__)


def create_trefle_searcher(
    api_token: str | None,
    base_url: str,
) -> Callable[[str], List[Dict[str, str]]]:
    def search(common_name: str) -> List[Dict[str, str]]:
        if not api_token:
            raise ValueError("Trefle API token is required")
        query = quote(common_name)
        url = f"{base_url.rstrip('/')}/api/v1/plants/search?q={query}&token={api_token}"
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

    return search


def trefle_search(common_name: str) -> List[Dict[str, str]]:
    api_token = os.getenv("TREFLE_API_TOKEN")
    base_url = os.getenv("TREFLE_API_BASE", "https://trefle.io")
    return create_trefle_searcher(api_token, base_url)(common_name)
