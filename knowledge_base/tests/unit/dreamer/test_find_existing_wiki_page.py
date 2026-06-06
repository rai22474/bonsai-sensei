from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from hamcrest import assert_that, equal_to

from knowledge_base.dreamer.find_existing_wiki_page import create_find_existing_wiki_page_tool


async def should_return_found_when_entity_name_in_page_content(wiki_root, embed, search_by_embedding):
    (wiki_root / "species" / "arce-tridente-japon-s.md").write_text(
        "# Arce tridente japonés\n*Acer buergerianum*\n\nContenido.", encoding="utf-8"
    )
    search_by_embedding.return_value = [("species/arce-tridente-japon-s.md", "abstract", 0.82)]
    find = create_find_existing_wiki_page_tool(embed, search_by_embedding, wiki_root)

    result = await find("Acer buergerianum", "species")

    assert_that(result["found"], equal_to(True))


async def should_return_page_path_of_matching_page(wiki_root, embed, search_by_embedding):
    (wiki_root / "species" / "arce-tridente-japon-s.md").write_text(
        "# Arce tridente japonés\n*Acer buergerianum*\n\nContenido.", encoding="utf-8"
    )
    search_by_embedding.return_value = [("species/arce-tridente-japon-s.md", "abstract", 0.82)]
    find = create_find_existing_wiki_page_tool(embed, search_by_embedding, wiki_root)

    result = await find("Acer buergerianum", "species")

    assert_that(result["page_path"], equal_to("species/arce-tridente-japon-s.md"))


async def should_return_not_found_when_entity_name_absent_from_content(wiki_root, embed, search_by_embedding):
    (wiki_root / "species" / "acer-palmatum.md").write_text(
        "# Acer palmatum\n\nOtra especie.", encoding="utf-8"
    )
    search_by_embedding.return_value = [("species/acer-palmatum.md", "abstract", 0.78)]
    find = create_find_existing_wiki_page_tool(embed, search_by_embedding, wiki_root)

    result = await find("Acer buergerianum", "species")

    assert_that(result["found"], equal_to(False))


async def should_skip_results_from_wrong_directory(wiki_root, embed, search_by_embedding):
    (wiki_root / "techniques" / "poda.md").write_text(
        "# Poda\nAcer buergerianum menciona poda.", encoding="utf-8"
    )
    search_by_embedding.return_value = [("techniques/poda.md", "abstract", 0.90)]
    find = create_find_existing_wiki_page_tool(embed, search_by_embedding, wiki_root)

    result = await find("Acer buergerianum", "species")

    assert_that(result["found"], equal_to(False))


async def should_skip_results_below_score_threshold(wiki_root, embed, search_by_embedding):
    (wiki_root / "species" / "arce-tridente-japon-s.md").write_text(
        "# Arce\n*Acer buergerianum*", encoding="utf-8"
    )
    search_by_embedding.return_value = [("species/arce-tridente-japon-s.md", "abstract", 0.49)]
    find = create_find_existing_wiki_page_tool(embed, search_by_embedding, wiki_root)

    result = await find("Acer buergerianum", "species")

    assert_that(result["found"], equal_to(False))


async def should_match_accented_entity_name(wiki_root, embed, search_by_embedding):
    (wiki_root / "diseases" / "roya.md").write_text(
        "# Roya\nLa roya es una enfermedad fúngica.", encoding="utf-8"
    )
    search_by_embedding.return_value = [("diseases/roya.md", "abstract", 0.85)]
    find = create_find_existing_wiki_page_tool(embed, search_by_embedding, wiki_root)

    result = await find("Roya", "diseases")

    assert_that(result["found"], equal_to(True))


@pytest.fixture
def wiki_root(tmp_path):
    (tmp_path / "species").mkdir()
    (tmp_path / "techniques").mkdir()
    (tmp_path / "diseases").mkdir()
    return tmp_path


@pytest.fixture
def embed():
    mock = AsyncMock()
    mock.return_value = [0.1] * 768
    return mock


@pytest.fixture
def search_by_embedding():
    return MagicMock(return_value=[])
