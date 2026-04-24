import pytest
from hamcrest import assert_that, equal_to

from bonsai_sensei.domain.services.cultivation.species import scientific_name_tool


def should_resolve_scientific_name_from_results(resolver_with_results):
    result = resolver_with_results("arce")

    assert_that(result["scientific_names"], equal_to(["Acer palmatum"]))


def should_use_translated_term_when_searching(resolver_with_translation):
    result = resolver_with_translation("pino negro japonés")

    assert_that(result["search_term"], equal_to("Japanese black pine"))


def should_return_empty_when_no_results(resolver_with_empty_results):
    result = resolver_with_empty_results("arce")

    assert_that(result["scientific_names"], equal_to([]))


def should_deduplicate_scientific_names(resolver_with_duplicates):
    result = resolver_with_duplicates("arce")

    assert_that(result["scientific_names"], equal_to(["Acer palmatum"]))


@pytest.fixture
def trefle_search_results():
    return [
        {
            "id": 123,
            "scientific_name": "Acer palmatum",
        }
    ]


@pytest.fixture
def empty_search_results():
    return []


@pytest.fixture
def duplicate_search_results():
    return [
        {
            "id": 1,
            "scientific_name": "Acer palmatum",
        },
        {
            "id": 2,
            "scientific_name": "Acer palmatum",
        },
    ]


@pytest.fixture
def resolver_with_results(trefle_search_results):
    resolver = scientific_name_tool.create_scientific_name_resolver(
        translator=lambda name: name,
        searcher=lambda common: trefle_search_results,
    )

    def wrapped(common_name: str):
        result = resolver(common_name)
        return {"scientific_names": result["scientific_names"]}

    return wrapped


@pytest.fixture
def resolver_with_translation(trefle_search_results):
    captured = {"search_term": ""}

    def searcher(common_name: str):
        captured["search_term"] = common_name
        return trefle_search_results

    resolver = scientific_name_tool.create_scientific_name_resolver(
        translator=lambda name: "Japanese black pine",
        searcher=searcher,
    )

    def wrapped(common_name: str):
        resolver(common_name)
        return {"search_term": captured["search_term"]}

    return wrapped


@pytest.fixture
def resolver_with_empty_results(empty_search_results):
    resolver = scientific_name_tool.create_scientific_name_resolver(
        translator=lambda name: name,
        searcher=lambda common: empty_search_results,
    )

    def wrapped(common_name: str):
        result = resolver(common_name)
        return {"scientific_names": result["scientific_names"]}

    return wrapped


@pytest.fixture
def resolver_with_duplicates(duplicate_search_results):
    resolver = scientific_name_tool.create_scientific_name_resolver(
        translator=lambda name: name,
        searcher=lambda common: duplicate_search_results,
    )

    def wrapped(common_name: str):
        result = resolver(common_name)
        return {"scientific_names": result["scientific_names"]}

    return wrapped