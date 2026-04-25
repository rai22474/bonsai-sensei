import re
import uuid
from pathlib import Path
from typing import Callable

from google.adk.agents.llm_agent import Agent
from google.adk.runners import InMemoryRunner, RunConfig
from google.genai import types

_APP_NAME = "wiki_compiler"
_MAX_LLM_CALLS = 20

_COMPILER_INSTRUCTION = """
Eres un compilador de conocimiento sobre bonsáis. Dado un nombre común y un nombre científico, tu tarea es investigar la especie y escribir una ficha de cultivo completa en markdown en castellano.

# Comportamiento
- Usa search_bonsai_info para buscar información: guía general, riego, luz, suelo, poda, plagas. Haz las búsquedas que consideres necesarias.
- Si el prompt incluye el contenido actual de la página, úsalo como base y consérvalo íntegramente salvo que sea incorrecto o el usuario pida explícitamente cambiarlo. Añade o amplía solo donde sea necesario para satisfacer la petición del usuario; el resto del contenido debe quedar tal como estaba.
- Si el prompt incluye instrucciones específicas del usuario, priorízalas al decidir qué investigar y qué secciones mejorar.
- Escribe la ficha con write_wiki_page cuando tengas suficiente información. Solo debes llamar a write_wiki_page una vez.
- Usa wikilinks [[relative/path.md]] si detectas enfermedades o tratamientos fitosanitarios relacionados con la especie.
- Incluye las URLs de las fuentes consultadas en una sección ## Fuentes al final.

# Formato de la ficha
La ficha debe comenzar con el nombre común como título H1 seguido del nombre científico en cursiva, un párrafo introductorio, y al menos las secciones: Riego, Luz, Suelo, Poda, Plagas y Fuentes. Puedes añadir secciones adicionales si el contenido lo justifica o el usuario lo solicita.
"""


def create_species_wiki_compiler(
    model: object,
    wiki_root: str | Path,
    searcher: Callable[[str], dict],
) -> Callable[[str, str, str], str]:
    """Create an async compiler that generates a markdown wiki page for a bonsai species.

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

    compiler_agent = Agent(
        model=model,
        name="wiki_compiler",
        instruction=_COMPILER_INSTRUCTION,
        tools=[search_tool, write_wiki_page],
    )

    async def compile_species_page(common_name: str, scientific_name: str, user_instructions: str = "") -> str:
        slug = _slugify(common_name)
        relative_path = f"species/{slug}.md"
        existing_content = _read_existing_page(wiki_root_path / relative_path)
        runner = InMemoryRunner(agent=compiler_agent, app_name=_APP_NAME)
        session_id = str(uuid.uuid4())
        await runner.session_service.create_session(
            app_name=_APP_NAME,
            user_id=_APP_NAME,
            session_id=session_id,
        )
        prompt = _build_compile_prompt(common_name, scientific_name, relative_path, existing_content, user_instructions)
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

    return compile_species_page


def create_write_wiki_page_tool(wiki_root: str | Path) -> Callable:
    """Create a tool that writes content to a wiki page at the given relative path.

    Args:
        wiki_root: Absolute path to the root directory of the wiki.
    """
    wiki_root_path = Path(wiki_root).resolve()

    def write_wiki_page(path: str, content: str) -> dict:
        """Write content to a wiki page at the given path relative to the wiki root.

        Creates parent directories if they do not exist.

        Args:
            path: Path relative to wiki root (e.g. 'species/ficus-retusa.md').
            content: Full markdown content to write to the page.

        Returns:
            A dict with status 'success' and 'path', or status 'error' and 'message'.
            Output JSON (success): {"status": "success", "path": "<relative_path>"}.
            Output JSON (error): {"status": "error", "message": "invalid_path"}.
        """
        resolved = (wiki_root_path / path).resolve()
        if not str(resolved).startswith(str(wiki_root_path)):
            return {"status": "error", "message": "invalid_path"}
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(content, encoding="utf-8")
        return {"status": "success", "path": path}

    return write_wiki_page


def _create_search_tool(searcher: Callable[[str], dict]) -> Callable:
    def search_bonsai_info(query: str) -> dict:
        """Search for information about bonsai species care and cultivation.

        Args:
            query: Search query string (e.g. 'Ficus retusa bonsai watering').

        Returns:
            A dict with 'answer' (str summary) and 'results' (list of dicts with 'url' and 'content').
        """
        return searcher(query)

    return search_bonsai_info


def _build_compile_prompt(common_name: str, scientific_name: str, relative_path: str, existing_content: str | None, user_instructions: str) -> str:
    parts = [f"Investiga y escribe la ficha wiki para {common_name} ({scientific_name}). Guárdala en la ruta: {relative_path}"]
    if existing_content:
        parts.append(f"\nContenido actual de la página:\n{existing_content}")
    if user_instructions:
        parts.append(f"\nInstrucciones específicas del usuario: {user_instructions}")
    return "\n".join(parts)


def _read_existing_page(path: Path) -> str | None:
    return path.read_text(encoding="utf-8") if path.exists() else None


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
