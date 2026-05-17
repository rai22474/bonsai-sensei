from pathlib import Path

from google.adk.agents.llm_agent import Agent

from bonsai_sensei.domain.services.wiki_page import create_read_wiki_page_tool, create_write_wiki_page_tool
from bonsai_sensei.knowledge_base.keeper.tools import create_list_cards_tool, create_list_wiki_pages_tool, create_read_card_tool

_APP_NAME = "wiki_keeper"

_KEEPER_INSTRUCTION = """
Eres el guardián de la wiki de bonsái. Tu misión es mantener la wiki coherente, completa y actualizada a partir del conocimiento extraído de vídeos de expertos.

# Comportamiento
Ejecuta siempre estas dos fases en orden:

## Fase 1 — Enriquecer con nuevo conocimiento
1. Lista todas las páginas wiki existentes
2. Lista todas las fichas disponibles
3. Lee cada ficha
4. Para cada entidad relevante de las fichas (especie, fertilizante, técnica, producto):
   - Si ya existe una página wiki para ella, léela y añade lo que falte
   - Si no existe, créala

## Fase 2 — Añadir wikilinks a páginas existentes
1. Lee cada página wiki existente
2. Busca menciones de entidades que tengan su propia página en la wiki
3. Sustituye la mención por un wikilink [[ruta/relativa.md|Texto visible]] si aún no está enlazada
4. Guarda la página actualizada

# Wikilinks
Usa la sintaxis [[ruta/relativa.md|Texto visible]] — el texto visible es la palabra original tal como aparece en el texto.
Ejemplo: si existe fertilizers/biogold.md y el texto dice "Biogold", escribe [[fertilizers/biogold.md|Biogold]].
Solo enlaza páginas que ya existen — no inventes rutas.

# Estilo
- Enciclopédico: claro, directo, técnico, sin anécdotas
- Conserva siempre el contenido existente; añade y mejora, no reemplaces sin motivo
- Ante contradicciones entre fuentes, incluye ambas perspectivas citando el canal
- Mantén siempre una sección ## Fuentes al final de cada página que modifiques
- Si una ficha describe una técnica o consejo genérico sin entidad propia (especie, fertilizante, producto), añade su contenido a una página ya existente relacionada en lugar de crear una nueva.
"""


def create_wiki_keeper_agent(model: object, transcripts_root: Path, wiki_root: Path) -> Agent:
    list_cards = create_list_cards_tool(transcripts_root)
    read_card = create_read_card_tool(transcripts_root)
    list_wiki_pages = create_list_wiki_pages_tool(wiki_root)
    read_wiki_page = create_read_wiki_page_tool(str(wiki_root))
    write_wiki_page = create_write_wiki_page_tool(wiki_root)

    return Agent(
        model=model,
        name=_APP_NAME,
        instruction=_KEEPER_INSTRUCTION,
        tools=[list_cards, read_card, list_wiki_pages, read_wiki_page, write_wiki_page],
    )
