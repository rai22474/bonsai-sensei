from typing import Callable

import aiohttp


def create_pest(post_func: Callable[[str, dict | None], dict | None], name: str) -> dict:
    return post_func("/api/pests", {"name": name}) or {}


def delete_pest_by_name(delete_func: Callable[[str], dict | None], name: str) -> None:
    try:
        delete_func(f"/api/pests/{name}")
    except aiohttp.ClientResponseError as exc:
        if exc.status == 404:
            return
        raise


def list_pests(get_func: Callable[[str], list | None]) -> list[dict]:
    return get_func("/api/pests") or []
