from typing import Callable, Optional, List
from bonsai_sensei.database.species import Species


def create_bonsai_species_tool(
    create_species_func: Callable[..., Species],
) -> Callable[
    [str, str, str, List[str], Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]],
    dict,
]:
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
        """Create a bonsai species record with a structured care guide payload."""
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


def _normalize_scientific_name(scientific_name: Optional[str]) -> Optional[str]:
    if scientific_name is None:
        return None

    trimmed = scientific_name.strip()
    return trimmed if trimmed else None
