from typing import Callable


def create_bonsai(
    post_func: Callable[[str, dict | None], dict | None],
    name: str,
    species_id: int,
    user_id: str | None = None,
) -> dict:
    payload = {"name": name, "species_id": species_id}
    if user_id:
        payload["user_id"] = user_id
    return post_func("/api/bonsai", payload) or {}


def list_bonsai(
    get_func: Callable[[str], dict | list | None],
    user_id: str | None = None,
) -> list[dict]:
    url = f"/api/bonsai?user_id={user_id}" if user_id else "/api/bonsai"
    items = get_func(url) or []
    return list(items)


def find_bonsai_by_name(
    get_func: Callable[[str], dict | list | None],
    name: str,
    user_id: str | None = None,
) -> dict | None:
    items = list_bonsai(get_func, user_id=user_id)
    normalized = name.casefold()
    for item in items:
        if item.get("name", "").casefold() == normalized:
            return item
    return None


def update_bonsai(
    put_func: Callable[[str, dict | None], dict | None],
    bonsai_id: int,
    payload: dict,
) -> dict:
    return put_func(f"/api/bonsai/{bonsai_id}", payload) or {}


def delete_bonsai_by_name(
    get_func: Callable[[str], dict | list | None],
    delete_func: Callable[[str], dict | None],
    name: str,
    user_id: str | None = None,
) -> None:
    bonsai = find_bonsai_by_name(get_func, name, user_id=user_id)
    if not bonsai:
        return
    delete_func(f"/api/bonsai/{bonsai['id']}")
