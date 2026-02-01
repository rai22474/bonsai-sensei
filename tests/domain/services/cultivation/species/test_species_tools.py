import pytest
from hamcrest import assert_that, equal_to

from bonsai_sensei.domain.species import Species
from bonsai_sensei.domain.services.cultivation.species.herbarium_tools import (
    create_species_tool,
    create_get_species_by_name_tool,
)


def should_return_needs_scientific_name_when_missing(create_tool, sample_guide):
    result = create_tool("arce", "", **sample_guide)

    assert_that(result["needs_scientific_name"], equal_to(True))


def should_return_created_name_when_created(create_tool, sample_guide):
    result = create_tool("arce", "Acer palmatum", **sample_guide)

    assert_that(result["created_name"], equal_to("arce"))


def should_return_care_guide_when_created(create_tool, sample_guide):
    result = create_tool("arce", "Acer palmatum", **sample_guide)

    assert_that(result["care_guide"], equal_to(sample_guide))


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
                    "care_guide": {"watering": "Regular"},
                },
            }
        ),
    )


@pytest.fixture
def create_species_func():
    def create_species(species: Species) -> Species:
        return species

    return create_species


@pytest.fixture
def create_tool(create_species_func):
    return create_species_tool(create_species_func)


@pytest.fixture
def get_species_tool():
    species_item = Species(
        id=1,
        name="Olmo",
        scientific_name="Ulmus",
        care_guide={"watering": "Regular"},
    )

    def get_species_by_name(name: str) -> Species | None:
        return species_item if name == species_item.name else None

    return create_get_species_by_name_tool(get_species_by_name)


@pytest.fixture
def sample_guide():
    return {
        "summary": "Guide summary",
        "sources": ["https://example.com"],
        "watering": "Water regularly",
        "light": "Bright indirect light",
        "soil": "Well-draining soil",
        "pruning": "Prune in spring",
        "pests": "Aphids",
    }


