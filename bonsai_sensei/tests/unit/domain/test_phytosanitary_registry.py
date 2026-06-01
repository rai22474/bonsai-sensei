import pytest
from sqlmodel import create_engine, Session, SQLModel
from hamcrest import assert_that, equal_to

from bonsai_sensei.domain.phytosanitary_registry import create_phytosanitary, get_phytosanitary_by_name
from bonsai_sensei.domain.phytosanitary import Phytosanitary


@pytest.fixture
def create_session(in_memory_engine):
    return lambda: Session(in_memory_engine, expire_on_commit=False)


def should_store_phytosanitary_name_in_lowercase(create_session):
    phytosanitary = Phytosanitary(name="Neem Oil")

    create_phytosanitary(phytosanitary=phytosanitary, create_session=create_session)

    assert_that(phytosanitary.name, equal_to("neem oil"), "Phytosanitary name must be lowercase after creation")


def should_find_phytosanitary_by_name_case_insensitively(create_session):
    create_phytosanitary(phytosanitary=Phytosanitary(name="fungicida"), create_session=create_session)

    result = get_phytosanitary_by_name(name="FUNGICIDA", create_session=create_session)

    assert_that(result.name, equal_to("fungicida"), "get_phytosanitary_by_name must find product regardless of input case")


def should_store_mixed_case_input_as_lowercase(create_session):
    create_phytosanitary(phytosanitary=Phytosanitary(name="AcaroKill"), create_session=create_session)

    result = get_phytosanitary_by_name(name="acarokill", create_session=create_session)

    assert_that(result.name, equal_to("acarokill"), "Mixed case input must be stored as lowercase")


@pytest.fixture(scope="module")
def in_memory_engine():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine, tables=[Phytosanitary.__table__])
    return engine
