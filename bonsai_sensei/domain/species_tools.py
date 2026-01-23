from typing import Callable
from bonsai_sensei.database.species import Species


def create_create_species_tool(create_species_func: Callable[..., Species]) -> Callable[[str, str], dict]:
    def create_species(common_name: str, scientific_name: str) -> dict:
        created = create_species_func(
            species=Species(
                name=common_name,
                care_guide={"scientific_name": scientific_name},
            )
        )
        return {
            "common_name": common_name,
            "scientific_name": scientific_name,
            "created_name": created.name,
        }

    return create_species