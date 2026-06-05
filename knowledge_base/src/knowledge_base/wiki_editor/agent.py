from pathlib import Path

from google.adk.agents.llm_agent import Agent
from google.adk.tools import FunctionTool
from jinja2 import ChoiceLoader, Environment, FileSystemLoader

from knowledge_base.wiki_editor.tools.read_page import read_wiki_page
from knowledge_base.wiki_editor.tools.write_page import write_wiki_page
from knowledge_base.wiki_editor.tools.list_pages import list_wiki_pages
from knowledge_base.wiki_editor.tools.search_pages import search_wiki_pages
from knowledge_base.wiki_editor.tools.replace_in_pages import replace_in_pages

_APP_NAME = "wiki_editor"

_templates_env = Environment(
    loader=ChoiceLoader([
        FileSystemLoader(str(Path(__file__).parent / "templates")),
        FileSystemLoader(str(Path(__file__).parent.parent / "templates")),
    ]),
    trim_blocks=True,
    lstrip_blocks=True,
)

_WIKI_EDITOR_INSTRUCTION = _templates_env.get_template("wiki_editor_instruction.jinja2").render()


def create_wiki_editor_agent(model: object, wiki_root: Path, web_searcher=None) -> Agent:
    def read_page(page_path: str) -> str:
        """Read the content of a wiki page. Returns the markdown content or an error message if not found."""
        return read_wiki_page(page_path, wiki_root)

    def write_page(page_path: str, content: str) -> str:
        """Write or update a wiki page with the given markdown content. Creates the file if it doesn't exist. Returns confirmation."""
        return write_wiki_page(page_path, content, wiki_root)

    def list_pages() -> str:
        """List all markdown pages in the wiki. Returns a newline-separated list of page paths."""
        return list_wiki_pages(wiki_root)

    def search_pages(pattern: str) -> str:
        """Search wiki pages using a regular expression (Python regex, case-insensitive). Returns matching lines as 'path:line_number:content'. Use this before reading pages to locate relevant content. Examples: 'Biorren', '\\bficus\\b', 'error.*página'."""
        return search_wiki_pages(pattern, wiki_root)

    def bulk_replace(pattern: str, replacement: str, max_pages: int = 5) -> str:
        """Replace all regex matches across wiki pages, processing up to max_pages per call.

        Use for bulk corrections: fixing misspellings, renaming entities, standardizing terms.
        Call repeatedly until it reports no more pages pending.

        Args:
            pattern: Python regex to search for (case-insensitive). E.g. 'Biorren', 'biogold'.
            replacement: Literal replacement string. E.g. 'Biorend', 'Biogold'.
            max_pages: Pages to fix in this call (default 5).
        """
        return replace_in_pages(pattern, replacement, wiki_root, max_pages)

    tools = [
        FunctionTool(func=read_page),
        FunctionTool(func=write_page),
        FunctionTool(func=list_pages),
        FunctionTool(func=search_pages),
        FunctionTool(func=bulk_replace),
    ]

    if web_searcher is not None:
        def search_web(query: str) -> str:
            """Search the web for information to complement or verify wiki content.

            Use when the wiki lacks information about a species, fertilizer, technique or product,
            or when the admin explicitly asks to search the web. Returns a summary and up to 5 sources.

            Args:
                query: Search query in Spanish or English. Be specific: e.g. 'Trichoderma harzianum bonsai benefits'.
            """
            return web_searcher(query)

        tools.append(FunctionTool(func=search_web))

    return Agent(
        model=model,
        name=_APP_NAME,
        instruction=_WIKI_EDITOR_INSTRUCTION,
        tools=tools,
    )
