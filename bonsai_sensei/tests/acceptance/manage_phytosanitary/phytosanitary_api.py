from typing import Callable
import aiohttp


def create_phytosanitary(
    post_func: Callable[[str, dict | None], dict | None],
    name: str,
    wiki_path: str | None = None,
    user_id: str | None = None,
) -> dict:
    payload = {"name": name, "wiki_path": wiki_path}
    if user_id:
        payload["user_id"] = user_id
    return post_func("/api/phytosanitary", payload) or {}


def list_phytosanitary(
    get_func: Callable[[str], dict | list | None],
    user_id: str | None = None,
) -> list[dict]:
    url = f"/api/phytosanitary?user_id={user_id}" if user_id else "/api/phytosanitary"
    items = get_func(url) or []
    return list(items)


def find_phytosanitary_by_name(
    get_func: Callable[[str], dict | list | None],
    name: str,
    user_id: str | None = None,
) -> dict | None:
    url = f"/api/phytosanitary/{name}"
    if user_id:
        url += f"?user_id={user_id}"
    try:
        return get_func(url)
    except aiohttp.ClientResponseError as exc:
        if exc.status == 404:
            return None
        raise


def delete_phytosanitary_by_name(
    delete_func: Callable[[str], dict | None],
    name: str,
    user_id: str | None = None,
) -> None:
    url = f"/api/phytosanitary/{name}"
    if user_id:
        url += f"?user_id={user_id}"
    try:
        delete_func(url)
    except aiohttp.ClientResponseError as exc:
        if exc.status == 404:
            return
        raise
