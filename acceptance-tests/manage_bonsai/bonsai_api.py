from typing import Callable


def create_bonsai(
    post_func: Callable[[str, dict | None], dict | None],
    name: str,
    species_id: int,
) -> dict:
    return post_func("/api/bonsai", {"name": name, "species_id": species_id}) or {}


def list_bonsai(get_func: Callable[[str], dict | list | None]) -> list[dict]:
    items = get_func("/api/bonsai") or []
    return list(items)


def find_bonsai_by_name(
    get_func: Callable[[str], dict | list | None],
    name: str,
) -> dict | None:
    items = list_bonsai(get_func)
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
) -> None:
    bonsai = find_bonsai_by_name(get_func, name)
    if not bonsai:
        return
    delete_func(f"/api/bonsai/{bonsai['id']}")
