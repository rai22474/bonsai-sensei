import pytest
from hamcrest import assert_that, equal_to

from bonsai_sensei.domain.phytosanitary import Phytosanitary
from bonsai_sensei.domain.services.storekeeper.phytosanitary.phytosanitary_tools import (
    create_get_phytosanitary_by_name_tool,
    create_list_phytosanitary_tool,
)


def should_create_phytosanitary(create_phytosanitary_tool):
    result = create_phytosanitary_tool(
        "Phytosanitary A",
        "Sheet A",
        "10 ml/L",
        "Oidio",
        ["https://example.com/phytosanitary-a"],
    )

    assert_that(result["status"], equal_to("success"))


def should_list_phytosanitary(list_phytosanitary_tool):
    result = list_phytosanitary_tool()

    assert_that(
        result,
        equal_to(
            {
                "status": "success",
                "phytosanitary": [
                    {
                        "id": 1,
                        "name": "Phytosanitary A",
                        "usage_sheet": "Sheet A",
                        "recommended_amount": "10 ml/L",
                        "recommended_for": "Oidio",
                        "sources": ["https://example.com/phytosanitary-a"],
                    }
                ],
            }
        ),
    )


def should_get_phytosanitary_by_name(get_phytosanitary_tool):
    result = get_phytosanitary_tool("Phytosanitary A")

    assert_that(
        result,
        equal_to(
            {
                "status": "success",
                "phytosanitary": {
                    "id": 1,
                    "name": "Phytosanitary A",
                    "usage_sheet": "Sheet A",
                    "recommended_amount": "10 ml/L",
                    "recommended_for": "Oidio",
                    "sources": ["https://example.com/phytosanitary-a"],
                },
            }
        ),
    )


@pytest.fixture
def create_phytosanitary_func():
    def create_phytosanitary(phytosanitary: Phytosanitary) -> Phytosanitary:
        phytosanitary.id = 1
        return phytosanitary

    return create_phytosanitary


@pytest.fixture
def list_phytosanitary_func():
    def list_phytosanitary() -> list[Phytosanitary]:
        return [
            Phytosanitary(
                id=1,
                name="Phytosanitary A",
                usage_sheet="Sheet A",
                recommended_amount="10 ml/L",
                recommended_for="Oidio",
                sources=["https://example.com/phytosanitary-a"],
            )
        ]

    return list_phytosanitary


@pytest.fixture
def get_phytosanitary_by_name_func():
    def get_phytosanitary_by_name(name: str) -> Phytosanitary | None:
        if name == "Phytosanitary A":
            return Phytosanitary(
                id=1,
                name="Phytosanitary A",
                usage_sheet="Sheet A",
                recommended_amount="10 ml/L",
                recommended_for="Oidio",
                sources=["https://example.com/phytosanitary-a"],
            )
        return None

    return get_phytosanitary_by_name


@pytest.fixture
def create_phytosanitary_tool(create_phytosanitary_func):
    def create_phytosanitary(
        name: str,
        usage_sheet: str,
        recommended_amount: str,
        recommended_for: str,
        sources: list[str] | None = None,
    ) -> dict:
        if not name:
            return {"status": "error", "message": "phytosanitary_name_required"}
        if not usage_sheet:
            return {"status": "error", "message": "usage_sheet_required"}
        if not recommended_amount:
            return {"status": "error", "message": "recommended_amount_required"}
        if not recommended_for:
            return {"status": "error", "message": "recommended_for_required"}
        if sources is None:
            sources = []
        created = create_phytosanitary_func(
            Phytosanitary(
                name=name,
                usage_sheet=usage_sheet,
                recommended_amount=recommended_amount,
                recommended_for=recommended_for,
                sources=sources,
            )
        )
        return {
            "status": "success",
            "phytosanitary": {
                "id": created.id,
                "name": created.name,
                "usage_sheet": created.usage_sheet,
                "recommended_amount": created.recommended_amount,
                "recommended_for": created.recommended_for,
                "sources": created.sources,
            },
        }

    return create_phytosanitary


@pytest.fixture
def list_phytosanitary_tool(list_phytosanitary_func):
    return create_list_phytosanitary_tool(list_phytosanitary_func)


@pytest.fixture
def get_phytosanitary_tool(get_phytosanitary_by_name_func):
    return create_get_phytosanitary_by_name_tool(get_phytosanitary_by_name_func)