import pytest
from bonsai_sensei.domain.user_settings import UserSettings
from sqlmodel import create_engine, Session, SQLModel
from hamcrest import assert_that, equal_to

from bonsai_sensei.domain.fertilizer_catalog import create_fertilizer, get_fertilizer_by_name
from bonsai_sensei.domain.fertilizer import Fertilizer


@pytest.fixture
def create_session(in_memory_engine):
    return lambda: Session(in_memory_engine, expire_on_commit=False)


def should_store_fertilizer_name_in_lowercase(create_session):
    fertilizer = Fertilizer(name="GreenBoom")

    create_fertilizer(fertilizer=fertilizer, create_session=create_session)

    assert_that(fertilizer.name, equal_to("greenboom"), "Fertilizer name must be lowercase after creation")


def should_find_fertilizer_by_name_case_insensitively(create_session):
    create_fertilizer(fertilizer=Fertilizer(name="biogold"), create_session=create_session)

    result = get_fertilizer_by_name(name="BIOGOLD", create_session=create_session)

    assert_that(result.name, equal_to("biogold"), "get_fertilizer_by_name must find fertilizer regardless of input case")


def should_store_mixed_case_input_as_lowercase(create_session):
    create_fertilizer(fertilizer=Fertilizer(name="SuperGro"), create_session=create_session)

    result = get_fertilizer_by_name(name="supergro", create_session=create_session)

    assert_that(result.name, equal_to("supergro"), "Mixed case input must be stored as lowercase")


@pytest.fixture(scope="module")
def in_memory_engine():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine, tables=[UserSettings.__table__, Fertilizer.__table__])
    return engine
