from unittest.mock import AsyncMock, MagicMock

import pytest
from hamcrest import assert_that, equal_to, has_key

from knowledge_base.dreamer.search_wiki_knowledge import create_search_wiki_knowledge_tool


async def should_return_top_results_with_score(embed, search_by_embedding):
    search_by_embedding.return_value = [
        ("species/pinus-thunbergii.md", "Pino negro japonés.", 0.91),
    ]
    search = create_search_wiki_knowledge_tool(embed, search_by_embedding)

    result = await search("pino negro japonés especie")

    assert_that(result["results"][0]["score"], equal_to(0.91))


async def should_include_page_path_in_results(embed, search_by_embedding):
    search_by_embedding.return_value = [
        ("species/pinus-thunbergii.md", "Pino negro japonés.", 0.91),
    ]
    search = create_search_wiki_knowledge_tool(embed, search_by_embedding)

    result = await search("pino negro")

    assert_that(result["results"][0]["page_path"], equal_to("species/pinus-thunbergii.md"))


async def should_return_empty_list_when_no_results(embed, search_by_embedding):
    search_by_embedding.return_value = []
    search = create_search_wiki_knowledge_tool(embed, search_by_embedding)

    result = await search("entidad inexistente")

    assert_that(len(result["results"]), equal_to(0))


async def should_call_embed_with_query(embed, search_by_embedding):
    search_by_embedding.return_value = []
    search = create_search_wiki_knowledge_tool(embed, search_by_embedding)

    await search("roya enfermedad")

    embed.assert_awaited_once_with("roya enfermedad")


async def should_request_top_5_results(embed, search_by_embedding):
    search_by_embedding.return_value = []
    search = create_search_wiki_knowledge_tool(embed, search_by_embedding)

    await search("query")

    search_by_embedding.assert_called_once_with(embed.return_value, top_k=5)


@pytest.fixture
def embed():
    mock = AsyncMock()
    mock.return_value = [0.1] * 768
    return mock


@pytest.fixture
def search_by_embedding():
    return MagicMock(return_value=[])
