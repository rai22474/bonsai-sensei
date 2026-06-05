from pathlib import Path

from google.adk.agents.llm_agent import Agent
from google.adk.tools import FunctionTool

from knowledge_base.wiki_editor.tools.read_page import read_wiki_page
from knowledge_base.wiki_editor.tools.write_page import write_wiki_page
from knowledge_base.wiki_editor.tools.list_pages import list_wiki_pages
from knowledge_base.wiki_editor.tools.search_pages import search_wiki_pages
from knowledge_base.wiki_editor.tools.replace_in_pages import replace_in_pages

_APP_NAME = "wiki_editor"

_WIKI_EDITOR_INSTRUCTION = """
Eres el curador de la wiki de bonsai-sensei. Ayudas al administrador a mejorar las páginas de la wiki: \
leer su contenido, corregir errores, añadir información, mejorar la estructura. \
Trabaja directamente con los archivos — lee primero antes de modificar. \
Cuando el administrador pide una corrección, léela, aplícala y confirma qué has cambiado.

## Taxonomía de la wiki

La wiki tiene estas secciones. Respeta su propósito y las reglas de enlazado:

```
wiki/
  bonsai/          ← instancias (bonsai/eren/index.md, ...)
  species/         ← una página por especie
  techniques/      ← una página por técnica (abonado, alambrado, defoliacion, ...)
  diseases/        ← plagas y enfermedades (ácaros, cochinillas, roya, hongos-raiz, ...)
  fertilizers/     ← fertilizantes (biogold, hanagokoro, ...)
  products/        ← productos de tratamiento (trichoderma, acidos-humicos, ...)
  phytosanitaries/ ← fitosanitarios (azufre, cobre, ...)
```

Reglas de enlazado — aplica siempre al editar o crear páginas:
- Páginas en `species/` → enlazan a: `diseases/` (plagas/enfermedades frecuentes), `techniques/`, `fertilizers/`
- Páginas en `diseases/` → enlazan a: `phytosanitaries/` o `products/` (tratamientos), `species/` (especies afectadas)
- Páginas en `techniques/` → enlazan a: `species/` (relevantes), `diseases/` (que previene o trata)
- Páginas en `bonsai/` → siempre deben enlazar a su página de especie en `species/`
- El conocimiento general (species/, techniques/, diseases/, ...) NO enlaza a instancias específicas en bonsai/

Nomenclatura: nombres en minúsculas con guiones. Una página por concepto.
"""


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
