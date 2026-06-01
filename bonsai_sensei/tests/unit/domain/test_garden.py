import pytest
from sqlmodel import create_engine, Session, SQLModel
from hamcrest import assert_that, equal_to

from bonsai_sensei.domain.garden import create_bonsai, get_bonsai_by_name
from bonsai_sensei.domain.herbarium import create_species
from bonsai_sensei.domain.bonsai import Bonsai
from bonsai_sensei.domain.species import Species


@pytest.fixture
def create_session(in_memory_engine):
    return lambda: Session(in_memory_engine, expire_on_commit=False)


@pytest.fixture
def existing_species_id(create_session):
    species = create_species(species=Species(name="elm", scientific_name="Ulmus"), create_session=create_session)
    return species.id


def should_store_bonsai_name_in_lowercase(create_session, existing_species_id):
    bonsai = Bonsai(name="Naruto", species_id=existing_species_id)

    create_bonsai(bonsai=bonsai, create_session=create_session)

    assert_that(bonsai.name, equal_to("naruto"), "Bonsai name must be lowercase after creation")


def should_find_bonsai_by_name_case_insensitively(create_session, existing_species_id):
    create_bonsai(bonsai=Bonsai(name="shiro", species_id=existing_species_id), create_session=create_session)

    result = get_bonsai_by_name(name="SHIRO", create_session=create_session)

    assert_that(result.name, equal_to("shiro"), "get_bonsai_by_name must find bonsai regardless of input case")


def should_store_mixed_case_input_as_lowercase(create_session, existing_species_id):
    create_bonsai(bonsai=Bonsai(name="TanakaTree", species_id=existing_species_id), create_session=create_session)

    result = get_bonsai_by_name(name="tanakatree", create_session=create_session)

    assert_that(result.name, equal_to("tanakatree"), "Mixed case input must be stored as lowercase")


@pytest.fixture
def in_memory_engine():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine, tables=[Species.__table__, Bonsai.__table__])
    return engine
