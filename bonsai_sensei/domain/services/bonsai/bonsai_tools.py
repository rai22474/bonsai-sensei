from typing import Callable

from bonsai_sensei.database.bonsai import Bonsai
from bonsai_sensei.database.species import Species


def create_list_bonsai_tool(
    list_bonsai_func: Callable[[], list[Bonsai]],
    list_species_func: Callable[[], list[Species]],
):
    def list_bonsai() -> dict:
        bonsai_items = list_bonsai_func()
        if not bonsai_items:
            return {"status": "success", "bonsai": []}
        species_map = _build_species_map(list_species_func())
        items = [
            {
                "id": bonsai.id,
                "name": bonsai.name,
                "species_id": bonsai.species_id,
                "species_name": species_map.get(
                    bonsai.species_id, f"Especie {bonsai.species_id}"
                ),
            }
            for bonsai in bonsai_items
        ]
        return {"status": "success", "bonsai": items}

    list_bonsai.__doc__ = "List registered bonsai with their species names."
    return list_bonsai


def create_create_bonsai_tool(
    create_bonsai_func: Callable[[Bonsai], Bonsai | None],
    list_species_func: Callable[[], list[Species]],
):
    def create_bonsai(name: str, species_id: int) -> dict:
        if not name:
            return {"status": "error", "message": "bonsai_name_required"}
        if not species_id:
            return {"status": "error", "message": "species_id_required"}
        species_map = _build_species_map(list_species_func())
        if species_id not in species_map:
            return {"status": "error", "message": "species_not_found"}
        created = create_bonsai_func(bonsai=Bonsai(name=name, species_id=species_id))
        if not created:
            return {"status": "error", "message": "species_not_found"}
        return {
            "status": "success",
            "bonsai": {
                "id": created.id,
                "name": created.name,
                "species_id": created.species_id,
                "species_name": species_map.get(created.species_id, ""),
            },
        }

    create_bonsai.__doc__ = "Create a bonsai record for a specific species."
    return create_bonsai


def create_get_bonsai_by_name_tool(
    get_bonsai_by_name_func: Callable[[str], Bonsai | None],
    list_species_func: Callable[[], list[Species]],
):
    def get_bonsai_by_name(name: str) -> dict:
        if not name:
            return {"status": "error", "message": "bonsai_name_required"}
        bonsai = get_bonsai_by_name_func(name)
        if not bonsai:
            return {"status": "error", "message": "bonsai_not_found"}
        species_map = _build_species_map(list_species_func())
        species_name = species_map.get(
            bonsai.species_id, f"Especie {bonsai.species_id}"
        )
        return {
            "status": "success",
            "bonsai": {
                "id": bonsai.id,
                "name": bonsai.name,
                "species_id": bonsai.species_id,
                "species_name": species_name,
            },
        }

    get_bonsai_by_name.__doc__ = "Get a bonsai by name with its species."
    return get_bonsai_by_name


def create_update_bonsai_tool(
    update_bonsai_func: Callable[[int, dict], Bonsai | None],
    list_species_func: Callable[[], list[Species]],
):
    def update_bonsai(bonsai_id: int, name: str | None = None, species_id: int | None = None) -> dict:
        if not bonsai_id:
            return {"status": "error", "message": "bonsai_id_required"}
        species_map = _build_species_map(list_species_func())
        if species_id is not None and species_id not in species_map:
            return {"status": "error", "message": "species_not_found"}
        bonsai_data = {}
        if name is not None:
            bonsai_data["name"] = name
        if species_id is not None:
            bonsai_data["species_id"] = species_id
        if not bonsai_data:
            return {"status": "error", "message": "bonsai_update_required"}
        updated = update_bonsai_func(bonsai_id=bonsai_id, bonsai_data=bonsai_data)
        if not updated:
            return {"status": "error", "message": "bonsai_not_found"}
        return {
            "status": "success",
            "bonsai": {
                "id": updated.id,
                "name": updated.name,
                "species_id": updated.species_id,
                "species_name": species_map.get(updated.species_id, ""),
            },
        }

    return update_bonsai


def create_delete_bonsai_tool(delete_bonsai_func: Callable[[int], bool]):
    def delete_bonsai(bonsai_id: int) -> dict:
        if not bonsai_id:
            return {"status": "error", "message": "bonsai_id_required"}
        deleted = delete_bonsai_func(bonsai_id=bonsai_id)
        if not deleted:
            return {"status": "error", "message": "bonsai_not_found"}
        return {"status": "success", "bonsai_id": bonsai_id}

    return delete_bonsai


def _build_species_map(species_items: list[Species]) -> dict[int, str]:
    return {
        species.id: species.name
        for species in species_items
        if species.id is not None
    }
