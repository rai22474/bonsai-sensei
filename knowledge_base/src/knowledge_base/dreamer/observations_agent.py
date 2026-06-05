from pathlib import Path

from google.adk.agents.llm_agent import Agent
from jinja2 import Environment, FileSystemLoader

from knowledge_base.wiki_page_tools import create_read_wiki_page_tool, create_write_wiki_page_tool
from knowledge_base.dreamer.tools import create_list_wiki_pages_tool

APP_NAME = "wiki_dreamer_observations"

_templates_env = Environment(
    loader=FileSystemLoader(str(Path(__file__).parent / "templates")),
    trim_blocks=True,
    lstrip_blocks=True,
)


def create_observations_agent(model: object, wiki_root: Path) -> Agent:
    list_wiki_pages = create_list_wiki_pages_tool(wiki_root)
    read_wiki_page = create_read_wiki_page_tool(str(wiki_root))
    write_wiki_page = create_write_wiki_page_tool(wiki_root)
    return Agent(
        model=model,
        name=APP_NAME,
        instruction=_templates_env.get_template("observations_instruction.jinja2").render(),
        tools=[list_wiki_pages, read_wiki_page, write_wiki_page],
    )
