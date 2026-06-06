from hamcrest import assert_that, contains_string, not_none

from pytest_bdd import given, parsers, scenario, then, when

from http_client import post
from mcp_client import read_wiki_page, write_wiki_page

_SPECIES_CARD_CONTENT = """\
# Ficha de conocimiento

## Fuente
Canal: Test Channel

## Especies
- Ficus microcarpa: especie tropical de hoja perenne muy popular en bonsái. Tolera poda intensa y frecuente, lo que permite reducir con rapidez el tamaño de las hojas. Es ideal para principiantes por su gran capacidad de recuperación.

## Técnicas
- Poda de mantenimiento: en Ficus microcarpa se aplica durante todo el año exceptuando el invierno. Se eliminan las ramas que rompen la silueta y se reduce el crecimiento apical para distribuir la energía hacia las ramas inferiores.

## Temporadas
- Primavera: mejor época de trasplante y para hacer alambrado, cuando el árbol tiene plena actividad vegetativa.

## Consejos
- Regar abundantemente en verano cuando el sustrato esté casi seco. En invierno reducir el riego notablemente.
"""

_PODA_CARD_CONTENT = """\
# Ficha de conocimiento

## Fuente
Canal: Test Channel

## Técnicas
- Poda de mantenimiento: técnica fundamental para mantener la silueta del bonsái. Consiste en eliminar ramas cruzadas, ramas que crecen hacia el interior y chupones (brotes vigorosos que surgen del tronco o ramas principales sin respetar la estructura). Los chupones deben eliminarse en cuanto aparecen para que no consuman energía del árbol. La poda se realiza con tijeras bien afiladas y se aplica sellante en cortes mayores de 5mm.

## Consejos
- No podar en pleno verano salvo emergencia porque el árbol está bajo estrés térmico y los cortes tardan más en cicatrizar.
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
    assert_that(page.get("content", "").lower(), contains_string(text.lower()),
        f"Page {page_path} should contain '{text}'")


@then("the dreamer reports no changes")
def assert_no_changes(context):
    result = context.get("dreamer_result", {})
    assert_that(result.get("status"), contains_string("completed"),
        "Dreamer should complete without error even when skipping")
