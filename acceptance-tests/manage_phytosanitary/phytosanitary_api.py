from typing import Callable
import aiohttp


def create_phytosanitary(
    post_func: Callable[[str, dict | None], dict | None],
    name: str,
    usage_sheet: str,
    recommended_amount: str,
    recommended_for: str,
    sources: list[str],
) -> dict:
    payload = {
        "name": name,
        "usage_sheet": usage_sheet,
        "recommended_amount": recommended_amount,
        "recommended_for": recommended_for,
        "sources": sources,
    }
    return post_func("/api/phytosanitary", payload) or {}


def list_phytosanitary(get_func: Callable[[str], dict | list | None]) -> list[dict]:
    items = get_func("/api/phytosanitary") or []
    return list(items)


def find_phytosanitary_by_name(
    get_func: Callable[[str], dict | list | None],
    name: str,
) -> dict | None:
    try:
        return get_func(f"/api/phytosanitary/{name}")
    except aiohttp.ClientResponseError as exc:
        if exc.status == 404:
            return None
        raise
