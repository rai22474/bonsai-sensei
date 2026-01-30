import pytest
from hamcrest import assert_that, equal_to

from bonsai_sensei.database.bonsai import Bonsai
from bonsai_sensei.database.species import Species
from bonsai_sensei.domain.services.bonsai.bonsai_tools import (
    create_create_bonsai_tool,
    create_get_bonsai_by_name_tool,
    create_list_bonsai_tool,
)


def should_list_bonsai_with_species(list_bonsai_tool):
    result = list_bonsai_tool()

    assert_that(result, equal_to("Bonsáis registrados:\n- Olmo 1 (Olmo)"))


def should_create_bonsai(create_bonsai_tool):
    result = create_bonsai_tool("Olmo 1", 1)

    assert_that(result["status"], equal_to("success"))


def should_get_bonsai_by_name(get_bonsai_tool):
    result = get_bonsai_tool("Olmo 1")

    assert_that(result, equal_to("Bonsái: Olmo 1 (Olmo)"))


@pytest.fixture
def list_bonsai_tool():
    bonsai_items = [Bonsai(id=1, name="Olmo 1", species_id=1)]
    species_items = [Species(id=1, name="Olmo", scientific_name="Ulmus", care_guide={})]

    def list_bonsai():
        return bonsai_items

    def list_species():
        return species_items

    return create_list_bonsai_tool(list_bonsai, list_species)


@pytest.fixture
def create_bonsai_tool():
    created = []
    species_items = [Species(id=1, name="Olmo", scientific_name="Ulmus", care_guide={})]

    def list_species():
        return species_items

    def create_bonsai(bonsai: Bonsai) -> Bonsai | None:
        bonsai.id = len(created) + 1
        created.append(bonsai)
        return bonsai

    return create_create_bonsai_tool(create_bonsai, list_species)


@pytest.fixture
def get_bonsai_tool():
    bonsai_item = Bonsai(id=1, name="Olmo 1", species_id=1)
    species_items = [Species(id=1, name="Olmo", scientific_name="Ulmus", care_guide={})]

    def list_species():
        return species_items

    def get_bonsai_by_name(name: str) -> Bonsai | None:
        return bonsai_item if name == bonsai_item.name else None

    return create_get_bonsai_by_name_tool(get_bonsai_by_name, list_species)
