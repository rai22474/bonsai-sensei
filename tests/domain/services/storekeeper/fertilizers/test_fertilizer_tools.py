import pytest
from hamcrest import assert_that, equal_to

from bonsai_sensei.domain.fertilizer import Fertilizer
from bonsai_sensei.domain.services.storekeeper.fertilizers.fertilizer_tools import (
    create_get_fertilizer_by_name_tool,
    create_list_fertilizers_tool,
)


def should_list_fertilizers(list_fertilizers_tool):
    result = list_fertilizers_tool()

    assert_that(result, equal_to({
        "status": "success",
        "fertilizers": [{"id": 1, "name": "Fertilizer A"}],
    }), "Should list fertilizers with only id and name")


def should_get_fertilizer_by_name(get_fertilizer_tool):
    result = get_fertilizer_tool("Fertilizer A")

    assert_that(result, equal_to({
        "status": "success",
        "fertilizer": {
            "id": 1,
            "name": "Fertilizer A",
            "recommended_amount": "10 ml/L",
            "content": None,
        },
    }), "Should return fertilizer with id, name, recommended_amount and wiki content (None when file not found)")


def should_return_error_when_fertilizer_not_found(get_fertilizer_tool):
    result = get_fertilizer_tool("Unknown")

    assert_that(result, equal_to({"status": "error", "message": "fertilizer_not_found"}),
        "Should return fertilizer_not_found error for unknown name")


@pytest.fixture
def fertilizer_a():
    return Fertilizer(
        id=1,
        name="Fertilizer A",
        recommended_amount="10 ml/L",
        wiki_path="fertilizers/fertilizer-a.md",
    )


@pytest.fixture
def list_fertilizers_func(fertilizer_a):
    def list_fertilizers() -> list[Fertilizer]:
        return [fertilizer_a]

    return list_fertilizers


@pytest.fixture
def get_fertilizer_by_name_func(fertilizer_a):
    def get_fertilizer_by_name(name: str) -> Fertilizer | None:
        if name == "Fertilizer A":
            return fertilizer_a
        return None

    return get_fertilizer_by_name


@pytest.fixture
def list_fertilizers_tool(list_fertilizers_func):
    return create_list_fertilizers_tool(list_fertilizers_func)


@pytest.fixture
def get_fertilizer_tool(get_fertilizer_by_name_func, tmp_path):
    return create_get_fertilizer_by_name_tool(get_fertilizer_by_name_func, wiki_root=str(tmp_path))
