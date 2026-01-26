import pytest

from bonsai_sensei.domain.scientific_name_tool import create_scientific_name_resolver
from bonsai_sensei.domain.scientific_name_translator import translate_to_english
from bonsai_sensei.domain.scientific_name_searcher import trefle_search


@pytest.mark.integration
def should_resolve_scientific_name_for_japanese_maple(resolver):
    result = resolver("Japanese maple")

    assert "Acer palmatum" in result["scientific_names"]


@pytest.mark.integration
def should_resolve_scientific_name_for_chinese_juniper(resolver):
    result = resolver("Chinese juniper")

    assert "Juniperus chinensis" in result["scientific_names"]


@pytest.mark.integration
def should_resolve_scientific_name_for_japanese_black_pine(resolver):
    result = resolver("Japanese black pine")

    assert "Pinus thunbergii" in result["scientific_names"]


@pytest.mark.integration
def should_match_spanish_and_english_names_for_japanese_black_pine(resolver):
    english = resolver("Japanese black pine")
    spanish = resolver("pino negro japonés")

    assert set(english["scientific_names"]) == set(spanish["scientific_names"])


@pytest.fixture(scope="module")
def resolver():
    try:
        trefle_search("check")
    except ValueError:
        pytest.skip("TREFLE_API_TOKEN is required for integration tests")
    return create_scientific_name_resolver(
        translator=translate_to_english,
        searcher=trefle_search,
    )
