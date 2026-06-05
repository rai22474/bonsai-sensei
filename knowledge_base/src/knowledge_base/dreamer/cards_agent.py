from pathlib import Path
from typing import Callable, Optional

from google.adk.agents.llm_agent import Agent
from jinja2 import Environment, FileSystemLoader

from knowledge_base.wiki_page_tools import create_read_wiki_page_tool, create_write_wiki_page_tool
from knowledge_base.dreamer.tools import (
    create_list_cards_tool,
    create_list_wiki_pages_tool,
    create_read_card_tool,
    create_search_wiki_knowledge_tool,
)

APP_NAME = "wiki_dreamer_cards"

_templates_env = Environment(
    loader=FileSystemLoader(str(Path(__file__).parent / "templates")),
    trim_blocks=True,
    lstrip_blocks=True,
)


def create_cards_agent(
    model: object,
    transcripts_root: Path,
    wiki_root: Path,
    embed: Optional[Callable] = None,
    search_by_embedding: Optional[Callable] = None,
) -> Agent:
    list_cards = create_list_cards_tool(transcripts_root)
    read_card = create_read_card_tool(transcripts_root)
    read_wiki_page = create_read_wiki_page_tool(str(wiki_root))
    write_wiki_page = create_write_wiki_page_tool(wiki_root)

    if embed is not None and search_by_embedding is not None:
        search_wiki_knowledge = create_search_wiki_knowledge_tool(embed, search_by_embedding)
        tools = [list_cards, read_card, search_wiki_knowledge, read_wiki_page, write_wiki_page]
    else:
        list_wiki_pages = create_list_wiki_pages_tool(wiki_root)
        tools = [list_cards, read_card, list_wiki_pages, read_wiki_page, write_wiki_page]

    return Agent(
        model=model,
        name=APP_NAME,
        instruction=_templates_env.get_template("cards_instruction.jinja2").render(),
        tools=tools,
    )
