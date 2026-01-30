from typing import Callable, Optional, List

from bonsai_sensei.database.species import Species


def create_species_tool(
    create_species_func: Callable[..., Species],
):
    def create_bonsai_species(
        common_name: str,
        scientific_name: str,
        summary: str,
        sources: List[str],
        watering: Optional[str] = None,
        light: Optional[str] = None,
        soil: Optional[str] = None,
        pruning: Optional[str] = None,
        pests: Optional[str] = None,
    ) -> dict:
        """Create a species and return JSON with care guide details.

        Output JSON (success): {"common_name","scientific_name","created_name","care_guide":{...}}.
        Output JSON (error): {"common_name","scientific_name":null,"candidates":[],"needs_scientific_name":true}.
        """
        normalized_scientific = _normalize_scientific_name(scientific_name)
        if not normalized_scientific:
            return {
                "common_name": common_name,
                "scientific_name": None,
                "candidates": [],
                "needs_scientific_name": True,
            }
        care_guide_payload = {
            "summary": summary,
            "sources": sources,
            "watering": watering,
            "light": light,
            "soil": soil,
            "pruning": pruning,
            "pests": pests,
        }
        created = create_species_func(
            species=Species(
                name=common_name,
                scientific_name=normalized_scientific,
                care_guide=care_guide_payload,
            )
        )
        return {
            "common_name": common_name,
            "scientific_name": normalized_scientific,
            "created_name": created.name,
            "care_guide": care_guide_payload,
        }

    return create_bonsai_species


def create_list_species_tool(get_all_species_func):
    def list_bonsai_species() -> dict:
        """Return JSON with status and species list.

        Output JSON: {"status":"success","species":[{"common_name","scientific_name"}]}.
        """
        species_list = get_all_species_func()
        if not species_list:
            return {"status": "success", "species": []}
        items = [
            {
                "common_name": item["common_name"],
                "scientific_name": item["scientific_name"],
            }
            for item in species_list
        ]
        return {"status": "success", "species": items}

    return list_bonsai_species


def create_get_species_by_name_tool(
    get_species_by_name_func: Callable[[str], Species | None],
):
    def get_bonsai_species_by_name(name: str) -> dict:
        """Lookup a species by common name and return JSON with status and record.

        Output JSON (success): {"status":"success","species":{"id","common_name","scientific_name","care_guide"}}.
        Output JSON (error): {"status":"error","message": "..."}.
        """
        if not name:
            return {"status": "error", "message": "species_name_required"}
        species = get_species_by_name_func(name)
        if not species:
            return {"status": "error", "message": "species_not_found"}
        return {
            "status": "success",
            "species": {
                "id": species.id,
                "common_name": species.name,
                "scientific_name": species.scientific_name or "",
                "care_guide": species.care_guide or {},
            },
        }

    return get_bonsai_species_by_name


def create_update_bonsai_species_tool(
    update_species_func: Callable[[int, dict], Species | None],
):
    def update_bonsai_species(
        species_id: int,
        common_name: str | None = None,
        scientific_name: str | None = None,
    ) -> dict:
        """Update a species and return JSON with status and updated record.

        Output JSON (success): {"status":"success","species":{"id","common_name","scientific_name"}}.
        Output JSON (error): {"status":"error","message": "..."}.
        """
        if not species_id:
            return {"status": "error", "message": "species_id_required"}
        species_data = {}
        if common_name is not None:
            species_data["name"] = common_name
        if scientific_name is not None:
            species_data["scientific_name"] = scientific_name
        if not species_data:
            return {"status": "error", "message": "species_update_required"}
        updated = update_species_func(species_id=species_id, species_data=species_data)
        if not updated:
            return {"status": "error", "message": "species_not_found"}
        return {
            "status": "success",
            "species": {
                "id": updated.id,
                "common_name": updated.name,
                "scientific_name": updated.scientific_name or "",
            },
        }

    return update_bonsai_species


def create_delete_bonsai_species_tool(delete_species_func: Callable[[int], bool]):
    def delete_bonsai_species(species_id: int) -> dict:
        """Delete a species by id and return JSON with status and species_id.

        Output JSON (success): {"status":"success","species_id": <id>}.
        Output JSON (error): {"status":"error","message": "..."}.
        """
        if not species_id:
            return {"status": "error", "message": "species_id_required"}
        deleted = delete_species_func(species_id=species_id)
        if not deleted:
            return {"status": "error", "message": "species_not_found"}
        return {"status": "success", "species_id": species_id}

    return delete_bonsai_species


def _normalize_scientific_name(scientific_name: Optional[str]) -> Optional[str]:
    if scientific_name is None:
        return None

    trimmed = scientific_name.strip()
    return trimmed if trimmed else None
