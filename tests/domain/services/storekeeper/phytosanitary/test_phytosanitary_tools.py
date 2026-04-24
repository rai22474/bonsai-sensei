import pytest

from bonsai_sensei.domain.phytosanitary import Phytosanitary
from bonsai_sensei.domain.services.storekeeper.phytosanitary.phytosanitary_tools import (
    create_get_phytosanitary_by_name_tool,
    create_list_phytosanitary_tool,
)


def should_list_phytosanitary(list_phytosanitary_tool):
    result = list_phytosanitary_tool()

    assert result == {
        "status": "success",
        "phytosanitary": [
            {
                "id": 1,
                "name": "Phytosanitary A",
                "recommended_amount": "10 ml/L",
                "wiki_path": "phytosanitaries/phytosanitary-a.md",
            }
        ],
    }, "Should list phytosanitary with id, name, recommended_amount and wiki_path"


def should_get_phytosanitary_by_name(get_phytosanitary_tool):
    result = get_phytosanitary_tool("Phytosanitary A")

    assert result == {
        "status": "success",
        "phytosanitary": {
            "id": 1,
            "name": "Phytosanitary A",
            "recommended_amount": "10 ml/L",
            "wiki_path": "phytosanitaries/phytosanitary-a.md",
        },
    }, "Should return phytosanitary record with id, name, recommended_amount and wiki_path"


def should_return_error_when_phytosanitary_not_found(get_phytosanitary_tool):
    result = get_phytosanitary_tool("Unknown")

    assert result == {"status": "error", "message": "phytosanitary_not_found"}, \
        "Should return phytosanitary_not_found error for unknown name"


@pytest.fixture
def phytosanitary_a():
    return Phytosanitary(
        id=1,
        name="Phytosanitary A",
        recommended_amount="10 ml/L",
        wiki_path="phytosanitaries/phytosanitary-a.md",
    )


@pytest.fixture
def list_phytosanitary_func(phytosanitary_a):
    def list_phytosanitary() -> list[Phytosanitary]:
        return [phytosanitary_a]

    return list_phytosanitary


@pytest.fixture
def get_phytosanitary_by_name_func(phytosanitary_a):
    def get_phytosanitary_by_name(name: str) -> Phytosanitary | None:
        if name == "Phytosanitary A":
            return phytosanitary_a
        return None

    return get_phytosanitary_by_name


@pytest.fixture
def list_phytosanitary_tool(list_phytosanitary_func):
    return create_list_phytosanitary_tool(list_phytosanitary_func)


@pytest.fixture
def get_phytosanitary_tool(get_phytosanitary_by_name_func):
    return create_get_phytosanitary_by_name_tool(get_phytosanitary_by_name_func)
