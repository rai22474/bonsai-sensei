from hamcrest import assert_that, contains_string, not_none

from pytest_bdd import given, parsers, scenario, then, when

from http_client import post
from mcp_client import read_wiki_page, write_wiki_page

_SPECIES_CARD_CONTENT = """\
# Ficha de conocimiento

## Fuente
Canal: Test Channel

## Especies
- Ficus microcarpa: especie tropical de hoja perenne, tolera poda intensa

## Técnicas
- Poda de mantenimiento: eliminar ramas que rompen la silueta

## Temporadas
- Primavera: época de trasplante

## Consejos
- Regar abundantemente en verano
"""

_PODA_CARD_CONTENT = """\
# Ficha de conocimiento

## Fuente
Canal: Test Channel

## Técnicas
- Poda de mantenimiento: eliminar ramas cruzadas y chupones para mantener la silueta limpia del bonsái

## Consejos
- No podar en pleno verano salvo emergencia
"""


@scenario("../features/wiki_dreamer_cards.feature", "Dreamer enriches a species page from a new knowledge card")
def test_dreamer_creates_species_page():
    return None


@scenario("../features/wiki_dreamer_cards.feature", "Dreamer updates an existing page with new card information")
def test_dreamer_updates_existing_page():
    return None


@scenario("../features/wiki_dreamer_cards.feature", "Dreamer does not run when there are no new cards")
def test_dreamer_skips_when_no_cards():
    return None


@given(parsers.parse('a knowledge card about Ficus microcarpa exists at "{card_path}"'))
def create_species_card(context, card_path):
    post("/api/wiki/transcripts/cards", {"path": card_path, "content": _SPECIES_CARD_CONTENT})
    context["card_paths_created"].append(card_path)
    context["wiki_paths_created"].append("species/ficus-microcarpa.md")


@given(parsers.parse('a wiki page "{page_path}" exists with content "{content}"'))
def create_wiki_page(context, page_path, content):
    write_wiki_page(page_path, content.replace("\\n", "\n"))
    context["wiki_paths_created"].append(page_path)


@given(parsers.parse('a knowledge card about poda with chupones exists at "{card_path}"'))
def create_poda_card(context, card_path):
    post("/api/wiki/transcripts/cards", {"path": card_path, "content": _PODA_CARD_CONTENT})
    context["card_paths_created"].append(card_path)


@given("no new knowledge cards exist since the last dreamer run")
def no_new_cards(context):
    pass


@when("the wiki dreamer runs synchronously")
def run_dreamer(context):
    result = post("/api/wiki/transcripts/wiki-dreamer/run/sync")
    context["dreamer_result"] = result


@then(parsers.parse('the wiki page "{page_path}" exists'))
def assert_page_exists(context, page_path):
    if page_path not in context["wiki_paths_created"]:
        context["wiki_paths_created"].append(page_path)
    page = read_wiki_page(page_path)
    assert_that(page, not_none(), f"Wiki page {page_path} should exist after dreamer run")


@then(parsers.parse('the wiki page "{page_path}" contains "{text}"'))
def assert_page_contains(context, page_path, text):
    if page_path not in context["wiki_paths_created"]:
        context["wiki_paths_created"].append(page_path)
    page = read_wiki_page(page_path)
    assert_that(page, not_none(), f"Wiki page {page_path} should exist")
    assert_that(page.get("content", ""), contains_string(text),
        f"Page {page_path} should contain '{text}'")


@then("the dreamer reports no changes")
def assert_no_changes(context):
    result = context.get("dreamer_result", {})
    assert_that(result.get("status"), contains_string("completed"),
        "Dreamer should complete without error even when skipping")
