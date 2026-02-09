from typing import Callable
import aiohttp


def create_fertilizer(
    post_func: Callable[[str, dict | None], dict | None],
    name: str,
    usage_sheet: str,
    recommended_amount: str,
    sources: list[str],
) -> dict:
    payload = {
        "name": name,
        "usage_sheet": usage_sheet,
        "recommended_amount": recommended_amount,
        "sources": sources,
    }
    return post_func("/api/fertilizers", payload) or {}


def list_fertilizers(get_func: Callable[[str], dict | list | None]) -> list[dict]:
    items = get_func("/api/fertilizers") or []
    return list(items)


def find_fertilizer_by_name(
    get_func: Callable[[str], dict | list | None],
    name: str,
) -> dict | None:
    try:
        return get_func(f"/api/fertilizers/{name}")
    except aiohttp.ClientResponseError as exc:
        if exc.status == 404:
            return None
        raise
