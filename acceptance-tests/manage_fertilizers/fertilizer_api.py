from typing import Callable
import aiohttp


def create_fertilizer(
    post_func: Callable[[str, dict | None], dict | None],
    name: str,
    wiki_path: str | None = None,
) -> dict:
    payload = {"name": name, "wiki_path": wiki_path}
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


def delete_fertilizer_by_name(
    delete_func: Callable[[str], dict | None],
    name: str,
) -> None:
    try:
        delete_func(f"/api/fertilizers/{name}")
    except aiohttp.ClientResponseError as exc:
        if exc.status == 404:
            return
        raise
