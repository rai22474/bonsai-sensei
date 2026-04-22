import pytest
from hamcrest import assert_that, equal_to

from bonsai_sensei.domain.species import Species
from bonsai_sensei.domain.services.cultivation.species.herbarium_tools import (
    create_get_species_by_name_tool,
)


def should_return_species_by_name(get_species_tool):
    result = get_species_tool("Olmo")

    assert_that(
        result,
        equal_to(
            {
                "status": "success",
                "species": {
                    "id": 1,
                    "common_name": "Olmo",
                    "scientific_name": "Ulmus",
                    "wiki_path": "species/olmo.md",
                },
            }
        ),
        "Tool should return species with wiki_path",
    )


@pytest.fixture
def get_species_tool():
    species_item = Species(
        id=1,
        name="Olmo",
        scientific_name="Ulmus",
        wiki_path="species/olmo.md",
    )

    def get_species_by_name(name: str) -> Species | None:
        return species_item if name == species_item.name else None

    return create_get_species_by_name_tool(get_species_by_name)
