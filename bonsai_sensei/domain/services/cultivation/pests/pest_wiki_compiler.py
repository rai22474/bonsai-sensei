import re
import uuid
from pathlib import Path
from typing import Callable

from google.adk.agents.llm_agent import Agent
from google.adk.runners import InMemoryRunner, RunConfig
from google.genai import types

from bonsai_sensei.domain.services.wiki_page import create_write_wiki_page_tool

_APP_NAME = "pest_wiki_compiler"
_MAX_LLM_CALLS = 20

_COMPILER_INSTRUCTION = """
Eres un compilador de fichas técnicas de plagas para bonsáis. Dado el nombre de una plaga, tu tarea es investigar su biología y escribir una página wiki completa en markdown en castellano.

# Comportamiento
- Usa search_pest_info para buscar: biología y ciclo de vida, plantas hospedadoras, síntomas de infestación, métodos de control (orgánico y químico), prevención y fuentes.
- Si el prompt incluye instrucciones específicas del usuario, priorízalas al decidir qué investigar y qué secciones mejorar.
- Escribe la ficha con write_wiki_page cuando tengas suficiente información. Solo debes llamar a write_wiki_page una vez.
- Usa wikilinks [[../phytosanitaries/<slug>.md]] para los productos fitosanitarios que se usen para tratar esta plaga. Sustituye <slug> por el nombre del producto en minúsculas con guiones.
- Incluye las URLs de las fuentes consultadas en una sección ## Fuentes al final.

# Formato de la ficha
La ficha debe contener al menos las secciones: nombre de la plaga como título H1, párrafo introductorio, Biología y ciclo de vida, Síntomas, Plantas hospedadoras en bonsái, Control (tratamientos recomendados con wikilinks a productos), Prevención y Fuentes. Puedes añadir secciones adicionales si el contenido lo justifica.
"""


def create_pest_wiki_compiler(
    model: object,
    wiki_root: str | Path,
    searcher: Callable[[str], dict],
) -> Callable[[str, str], str]:
    """Create an async compiler that generates a markdown wiki page for a pest.

    Runs a dedicated ADK agent with Tavily search and wiki write tools.
    The agent decides what to search and how to structure the page.

    Args:
        model: LLM model to use for the compiler agent.
        wiki_root: Absolute path to the root directory of the wiki.
        searcher: Callable that accepts a search query and returns a dict with
            'answer' (str) and optional 'results' list of dicts with 'url' keys.
    """
    write_wiki_page = create_write_wiki_page_tool(wiki_root)
    search_tool = _create_search_tool(searcher)
    wiki_root_path = Path(wiki_root).resolve()

    async def compile_pest_page(name: str, user_instructions: str = "") -> str:
        slug = _slugify(name)
        relative_path = f"pests/{slug}.md"
        existing_content = _read_existing_page(wiki_root_path / relative_path)

        agent = Agent(
            model=model,
            name=_APP_NAME,
            instruction=_COMPILER_INSTRUCTION,
            tools=[search_tool, write_wiki_page],
        )
        runner = InMemoryRunner(agent=agent, app_name=_APP_NAME)
        session_id = str(uuid.uuid4())
        await runner.session_service.create_session(
            app_name=_APP_NAME,
            user_id=_APP_NAME,
            session_id=session_id,
        )
        prompt = _build_compile_prompt(name, relative_path, existing_content, user_instructions)
        message = types.Content(role="user", parts=[types.Part(text=prompt)])
        run_config = RunConfig(max_llm_calls=_MAX_LLM_CALLS)
        async for _ in runner.run_async(
            user_id=_APP_NAME,
            session_id=session_id,
            new_message=message,
            run_config=run_config,
        ):
            pass
        return relative_path

    return compile_pest_page


def _create_search_tool(searcher: Callable[[str], dict]) -> Callable:
    def search_pest_info(query: str) -> dict:
        """Search for pest information including biology, symptoms, and control methods for bonsai.

        Args:
            query: Search query string (e.g. 'araña roja bonsái síntomas tratamiento').

        Returns:
            A dict with 'answer' (str summary) and 'results' (list of dicts with 'url' and 'content').
        """
        return searcher(query)

    return search_pest_info


def _build_compile_prompt(name: str, relative_path: str, existing_content: str | None, user_instructions: str) -> str:
    parts = [f"Investiga y escribe la ficha wiki para la plaga {name} en bonsáis. Guárdala en la ruta: {relative_path}"]
    if existing_content:
        parts.append(f"\nContenido actual de la página:\n{existing_content}")
    if user_instructions:
        parts.append(f"\nInstrucciones específicas del usuario: {user_instructions}")
    return "\n".join(parts)


def _read_existing_page(path: Path) -> str | None:
    return path.read_text(encoding="utf-8") if path.exists() else None


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
