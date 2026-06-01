from pathlib import Path

from google.adk.agents.llm_agent import Agent
from google.adk.tools import FunctionTool

_APP_NAME = "wiki_editor"

_WIKI_EDITOR_INSTRUCTION = (
    "Eres el curador de la wiki de bonsai-sensei. Ayudas al administrador a mejorar las páginas de la wiki: "
    "leer su contenido, corregir errores, añadir información, mejorar la estructura. "
    "Trabaja directamente con los archivos — lee primero antes de modificar. "
    "Cuando el administrador pide una corrección, léela, aplícala y confirma qué has cambiado."
)


def read_wiki_page(page_path: str, wiki_root: Path) -> str:
    """Read the content of a wiki page. Returns the markdown content or an error message if not found."""
    wiki_root_resolved = wiki_root.resolve()
    resolved = (wiki_root_resolved / page_path).resolve()
    if not str(resolved).startswith(str(wiki_root_resolved)):
        return "Error: invalid path"
    if not resolved.exists():
        return f"Error: page '{page_path}' not found"
    return resolved.read_text(encoding="utf-8")


def write_wiki_page(page_path: str, content: str, wiki_root: Path) -> str:
    """Write or update a wiki page with the given markdown content. Creates the file if it doesn't exist. Returns confirmation."""
    wiki_root_resolved = wiki_root.resolve()
    resolved = (wiki_root_resolved / page_path).resolve()
    if not str(resolved).startswith(str(wiki_root_resolved)):
        return "Error: invalid path"
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(content, encoding="utf-8")
    return f"Page '{page_path}' written successfully"


def list_wiki_pages(wiki_root: Path) -> str:
    """List all markdown pages in the wiki. Returns a newline-separated list of page paths."""
    wiki_root_resolved = wiki_root.resolve()
    if not wiki_root_resolved.exists():
        return ""
    pages = sorted(str(page.relative_to(wiki_root_resolved)) for page in wiki_root_resolved.rglob("*.md"))
    return "\n".join(pages)


def search_wiki_pages(pattern: str, wiki_root: Path) -> str:
    """Search wiki pages using a regular expression. Returns matching lines as 'path:line_number:content'. Case-insensitive. Pattern is a Python regex (e.g. 'Biorren|biorren', '\\bficus\\b', 'error.*página')."""
    import re
    wiki_root_resolved = wiki_root.resolve()
    if not wiki_root_resolved.exists():
        return "No results found."
    try:
        compiled = re.compile(pattern, re.IGNORECASE)
    except re.error as regex_error:
        return f"Invalid regex pattern: {regex_error}"
    results = []
    for page in sorted(wiki_root_resolved.rglob("*.md")):
        relative_path = str(page.relative_to(wiki_root_resolved))
        for line_number, line in enumerate(page.read_text(encoding="utf-8").splitlines(), start=1):
            if compiled.search(line):
                results.append(f"{relative_path}:{line_number}:{line}")
    return "\n".join(results) if results else "No results found."


def create_wiki_editor_agent(model: object, wiki_root: Path) -> Agent:
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

    return Agent(
        model=model,
        name=_APP_NAME,
        instruction=_WIKI_EDITOR_INSTRUCTION,
        tools=[FunctionTool(func=read_page), FunctionTool(func=write_page), FunctionTool(func=list_pages), FunctionTool(func=search_pages)],
    )
