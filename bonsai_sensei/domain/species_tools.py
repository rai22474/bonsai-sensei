from typing import Callable, Optional
from bonsai_sensei.database.species import Species


def create_create_species_tool(
    create_species_func: Callable[..., Species],
) -> Callable[[str, str], dict]:
    def create_species(
        common_name: str,
        scientific_name: str,
    ) -> dict:
        normalized_scientific = _normalize_scientific_name(scientific_name)
        if not normalized_scientific:
            return {
                "common_name": common_name,
                "scientific_name": None,
                "candidates": [],
                "needs_scientific_name": True,
            }
        created = create_species_func(
            species=Species(
                name=common_name,
                care_guide=None,
            )
        )
        return {
            "common_name": common_name,
            "scientific_name": normalized_scientific,
            "created_name": created.name,
        }

    return create_species


def _normalize_scientific_name(scientific_name: Optional[str]) -> Optional[str]:
    if scientific_name is None:
        return None

    trimmed = scientific_name.strip()
    return trimmed if trimmed else None
