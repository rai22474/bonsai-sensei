import pytest

from bonsai_sensei.database.species import Species
from bonsai_sensei.domain.species_tools import create_create_species_tool


def should_return_needs_scientific_name_when_missing(create_tool):
    result = create_tool("arce", "")

    assert result["needs_scientific_name"] is True


def should_return_created_name_when_created(create_tool):
    result = create_tool("arce", "Acer palmatum")

    assert result["created_name"] == "arce"


@pytest.fixture
def create_species_func():
    def create_species(species: Species) -> Species:
        return species

    return create_species


@pytest.fixture
def create_tool(create_species_func):
    return create_create_species_tool(create_species_func)


