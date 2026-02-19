import pytest
from hamcrest import assert_that, equal_to

from bonsai_sensei.domain.fertilizer import Fertilizer
from bonsai_sensei.domain.services.storekeeper.fertilizers.fertilizer_tools import (
    create_get_fertilizer_by_name_tool,
    create_list_fertilizers_tool,
)


def should_create_fertilizer(create_fertilizer_tool):
    result = create_fertilizer_tool(
        "Fertilizer A",
        "Sheet A",
        "10 ml/L",
        ["https://example.com/fertilizer-a"],
    )

    assert_that(result["status"], equal_to("success"))


def should_list_fertilizers(list_fertilizers_tool):
    result = list_fertilizers_tool()

    assert_that(
        result,
        equal_to(
            {
                "status": "success",
                "fertilizers": [
                    {
                        "id": 1,
                        "name": "Fertilizer A",
                        "usage_sheet": "Sheet A",
                        "recommended_amount": "10 ml/L",
                        "sources": ["https://example.com/fertilizer-a"],
                    }
                ],
            }
        ),
    )


def should_get_fertilizer_by_name(get_fertilizer_tool):
    result = get_fertilizer_tool("Fertilizer A")

    assert_that(
        result,
        equal_to(
            {
                "status": "success",
                "fertilizer": {
                    "id": 1,
                    "name": "Fertilizer A",
                    "usage_sheet": "Sheet A",
                    "recommended_amount": "10 ml/L",
                    "sources": ["https://example.com/fertilizer-a"],
                },
            }
        ),
    )


@pytest.fixture
def create_fertilizer_func():
    def create_fertilizer(fertilizer: Fertilizer) -> Fertilizer:
        fertilizer.id = 1
        return fertilizer

    return create_fertilizer


@pytest.fixture
def list_fertilizers_func():
    def list_fertilizers() -> list[Fertilizer]:
        return [
            Fertilizer(
                id=1,
                name="Fertilizer A",
                usage_sheet="Sheet A",
                recommended_amount="10 ml/L",
                sources=["https://example.com/fertilizer-a"],
            )
        ]

    return list_fertilizers


@pytest.fixture
def get_fertilizer_by_name_func():
    def get_fertilizer_by_name(name: str) -> Fertilizer | None:
        if name == "Fertilizer A":
            return Fertilizer(
                id=1,
                name="Fertilizer A",
                usage_sheet="Sheet A",
                recommended_amount="10 ml/L",
                sources=["https://example.com/fertilizer-a"],
            )
        return None

    return get_fertilizer_by_name


@pytest.fixture
def create_fertilizer_tool(create_fertilizer_func):
    def create_fertilizer(
        name: str,
        usage_sheet: str,
        recommended_amount: str,
        sources: list[str] | None = None,
    ) -> dict:
        if not name:
            return {"status": "error", "message": "fertilizer_name_required"}
        if not usage_sheet:
            return {"status": "error", "message": "usage_sheet_required"}
        if not recommended_amount:
            return {"status": "error", "message": "recommended_amount_required"}
        if sources is None:
            sources = []
        created = create_fertilizer_func(
            Fertilizer(
                name=name,
                usage_sheet=usage_sheet,
                recommended_amount=recommended_amount,
                sources=sources,
            )
        )
        return {
            "status": "success",
            "fertilizer": {
                "id": created.id,
                "name": created.name,
                "usage_sheet": created.usage_sheet,
                "recommended_amount": created.recommended_amount,
                "sources": created.sources,
            },
        }

    return create_fertilizer


@pytest.fixture
def list_fertilizers_tool(list_fertilizers_func):
    return create_list_fertilizers_tool(list_fertilizers_func)


@pytest.fixture
def get_fertilizer_tool(get_fertilizer_by_name_func):
    return create_get_fertilizer_by_name_tool(get_fertilizer_by_name_func)