import pytest
from sqlmodel import create_engine, Session, SQLModel
from hamcrest import assert_that, equal_to

from bonsai_sensei.domain.herbarium import create_species, get_species_by_name
from bonsai_sensei.domain.species import Species

import bonsai_sensei.domain.species  # noqa: F401 — registers Species table in metadata


@pytest.fixture
def create_session(in_memory_engine):
    return lambda: Session(in_memory_engine, expire_on_commit=False)


def should_store_species_name_in_lowercase(create_session):
    species = Species(name="Elm", scientific_name="Ulmus")

    create_species(species=species, create_session=create_session)

    assert_that(species.name, equal_to("elm"), "Species name must be lowercase after creation")


def should_find_species_by_name_case_insensitively(create_session):
    create_species(species=Species(name="oak", scientific_name="Quercus"), create_session=create_session)

    result = get_species_by_name(name="OAK", create_session=create_session)

    assert_that(result.name, equal_to("oak"), "get_species_by_name must find species regardless of input case")


def should_store_uppercase_input_as_lowercase(create_session):
    create_species(species=Species(name="FICUS", scientific_name="Ficus retusa"), create_session=create_session)

    result = get_species_by_name(name="ficus", create_session=create_session)

    assert_that(result.name, equal_to("ficus"), "Uppercase input must be stored as lowercase")


@pytest.fixture(scope="module")
def in_memory_engine():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine, tables=[Species.__table__])
    return engine
