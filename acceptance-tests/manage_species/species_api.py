from typing import Callable
import aiohttp


def find_species_by_name(get_func: Callable[[str], dict | list | None], name: str) -> dict | None:
    try:
        items = get_func(f"/api/species/search?name={name}") or []
    except aiohttp.ClientResponseError as exc:
        if exc.status == 404:
            return None
        raise
    if not items:
        return None
    normalized = name.casefold()
    for item in items:
        if item.get("name", "").casefold() == normalized:
            return item
    return items[0]


def create_species(
    post_func: Callable[[str, dict | None], dict | None],
    name: str,
    scientific_name: str,
) -> dict:
    payload = {
        "name": name,
        "scientific_name": scientific_name,
        "care_guide": {
            "summary": "Guía de prueba.",
            "temperature_range_celsius": {"min": -2, "max": 25},
        },
    }
    return post_func("/api/species", payload) or {}


def update_species(
    post_func: Callable[[str, dict | None], dict | None],
    species_id: int,
    payload: dict,
) -> dict:
    return post_func(f"/api/species/{species_id}", payload) or {}


def delete_species_by_name(
    get_func: Callable[[str], dict | list | None],
    delete_func: Callable[[str], dict | None],
    name: str,
) -> None:
    species = find_species_by_name(get_func, name)
    if not species:
        return
    delete_func(f"/api/species/{species['id']}")


def get_species_id(
    get_func: Callable[[str], dict | list | None],
    context: dict,
    name: str,
) -> int:
    existing = context["species_ids"].get(name)
    if existing is not None:
        return existing
    species = find_species_by_name(get_func, name)
    if species is None:
        raise ValueError(f"species_not_found:{name}")
    species_id = species.get("id")
    context["species_ids"][name] = species_id
    return species_id
