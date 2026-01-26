import pytest

from bonsai_sensei.database.species import Species
from bonsai_sensei.domain.create_bonsai_species_tool import create_bonsai_species_tool


def should_return_needs_scientific_name_when_missing(create_tool, sample_guide):
    result = create_tool("arce", "", **sample_guide)

    assert result["needs_scientific_name"] is True


def should_return_created_name_when_created(create_tool, sample_guide):
    result = create_tool("arce", "Acer palmatum", **sample_guide)

    assert result["created_name"] == "arce"


def should_return_care_guide_when_created(create_tool, sample_guide):
    result = create_tool("arce", "Acer palmatum", **sample_guide)

    assert result["care_guide"] == sample_guide


@pytest.fixture
def create_species_func():
    def create_species(species: Species) -> Species:
        return species

    return create_species


@pytest.fixture
def create_tool(create_species_func):
    return create_bonsai_species_tool(create_species_func)


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


