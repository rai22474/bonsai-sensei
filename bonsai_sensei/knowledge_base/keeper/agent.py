from pathlib import Path

from google.adk.agents.llm_agent import Agent

from bonsai_sensei.domain.services.cultivation.species.species_wiki_compiler import create_write_wiki_page_tool
from bonsai_sensei.domain.services.wiki_page import create_read_wiki_page_tool
from bonsai_sensei.knowledge_base.keeper.tools import create_list_cards_tool, create_list_wiki_pages_tool, create_read_card_tool

_APP_NAME = "wiki_keeper"

_KEEPER_INSTRUCTION = """
Eres el guardián de la wiki de bonsái. Tu misión es mantener la wiki coherente, completa y actualizada a partir del conocimiento extraído de vídeos de expertos.

# Comportamiento
- Usa list_cards para obtener todas las fichas de conocimiento disponibles (fuente principal)
- Lee cada ficha con read_card para conocer el conocimiento disponible
- Usa list_wiki_pages para ver qué páginas temáticas existen en la wiki
- Lee las páginas wiki existentes con read_wiki_page antes de modificarlas
- Actualiza o crea páginas wiki temáticas (species/, fertilizers/, techniques/, etc.) con write_wiki_page
- Mantén un estilo enciclopédico: claro, directo, técnico, sin anécdotas
- Conserva siempre el contenido existente; añade y mejora, no reemplaces sin motivo
- Ante contradicciones entre fuentes distintas, incluye ambas perspectivas citando el canal de origen
- Al final de cada página que modifiques, mantén o añade una sección ## Fuentes con los canales y URLs que la sustentan
- Si una especie, técnica o producto aparece en las fichas pero no tiene página propia en la wiki, créala
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
