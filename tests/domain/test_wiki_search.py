from functools import partial

import pytest
from hamcrest import assert_that, equal_to

from bonsai_sensei.domain.services.wiki_search import create_search_wiki_knowledge_tool
from bonsai_sensei.knowledge_base.wiki_index.entry import IndexEntry
from bonsai_sensei.knowledge_base.wiki_index.searcher import search_by_embedding
from bonsai_sensei.knowledge_base.wiki_index.store import load_all_entries, save_entry


async def should_call_embed_and_return_results(wiki_root):
    entry = IndexEntry(page_path="species/ficus.md", abstract="Ficus retusa tropical species.", links=[], embedding=[1.0, 0.0, 0.0])
    save_entry(wiki_root, entry)

    async def mock_embed(text: str) -> list[float]:
        return [1.0, 0.0, 0.0]

    entry_loader = partial(load_all_entries, wiki_root)
    search_index = partial(search_by_embedding, load_entries=entry_loader)
    search_tool = create_search_wiki_knowledge_tool(mock_embed, search_index)

    result = await search_tool("ficus")

    assert_that(result["results"][0]["page_path"], equal_to("species/ficus.md"), "Tool should return the matching page path")


@pytest.fixture
def wiki_root(tmp_path):
    return tmp_path
