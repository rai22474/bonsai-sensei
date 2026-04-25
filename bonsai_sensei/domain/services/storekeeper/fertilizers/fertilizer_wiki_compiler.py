import re
import uuid
from pathlib import Path
from typing import Callable

from google.adk.agents.llm_agent import Agent
from google.adk.runners import InMemoryRunner, RunConfig
from google.genai import types

from bonsai_sensei.domain.services.cultivation.species.species_wiki_compiler import (
    create_write_wiki_page_tool,
)

_APP_NAME = "fertilizer_wiki_compiler"
_MAX_LLM_CALLS = 20

_COMPILER_INSTRUCTION = """
Eres un compilador de fichas técnicas de fertilizantes para bonsáis. Dado el nombre de un producto, tu tarea es investigar su ficha técnica y escribir una página wiki completa en markdown en castellano.

# Comportamiento
- Usa search_fertilizer_info para buscar: composición NPK, dosis de uso, época de aplicación, modo de aplicación, precauciones y fuentes.
- Si el prompt incluye el contenido actual de la página, úsalo como base y consérvalo íntegramente salvo que sea incorrecto o el usuario pida explícitamente cambiarlo. Añade o amplía solo donde sea necesario para satisfacer la petición del usuario; el resto del contenido debe quedar tal como estaba.
- Si el prompt incluye instrucciones específicas del usuario, priorízalas al decidir qué investigar y qué secciones mejorar.
- Escribe la ficha con write_wiki_page cuando tengas suficiente información. Solo debes llamar a write_wiki_page una vez.
- Llama a set_recommended_amount con la dosis de uso más concisa que hayas encontrado, expresada SIEMPRE en unidades métricas (e.g. "5 ml/L", "2 g por litro"). Si la fuente indica una medida informal como "una tapita", conviértela a mililitros usando el volumen estándar de tapón (≈5 ml). DEBES llamar a esta herramienta antes de terminar.
- Incluye las URLs de las fuentes consultadas en una sección ## Fuentes al final.

# Formato de la ficha
La ficha debe contener al menos las secciones: nombre del producto como título H1, párrafo introductorio, Composición NPK, Dosis recomendada, Época de aplicación, Modo de aplicación, Precauciones y Fuentes. Puedes añadir secciones adicionales si el contenido lo justifica o el usuario lo solicita.
"""


def create_fertilizer_wiki_compiler(
    model: object,
    wiki_root: str | Path,
    searcher: Callable[[str], dict],
) -> Callable[[str, str], tuple[str, str]]:
    """Create an async compiler that generates a markdown wiki page for a fertilizer.

    Runs a dedicated ADK agent with Tavily search, wiki write, and amount capture tools.
    The agent decides what to search, how to structure the page, and extracts the recommended amount.

    Args:
        model: LLM model to use for the compiler agent.
        wiki_root: Absolute path to the root directory of the wiki.
        searcher: Callable that accepts a search query and returns a dict with
            'answer' (str) and optional 'results' list of dicts with 'url' keys.
    """
    write_wiki_page = create_write_wiki_page_tool(wiki_root)
    search_tool = _create_search_tool(searcher)
    wiki_root_path = Path(wiki_root).resolve()

    async def compile_fertilizer_page(name: str, user_instructions: str = "") -> tuple[str, str]:
        slug = _slugify(name)
        relative_path = f"fertilizers/{slug}.md"
        existing_content = _read_existing_page(wiki_root_path / relative_path)
        captured = {"recommended_amount": "No disponible"}

        set_amount_tool = _create_set_recommended_amount_tool(captured)
        agent = Agent(
            model=model,
            name=_APP_NAME,
            instruction=_COMPILER_INSTRUCTION,
            tools=[search_tool, write_wiki_page, set_amount_tool],
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
        return relative_path, captured["recommended_amount"]

    return compile_fertilizer_page


def _create_search_tool(searcher: Callable[[str], dict]) -> Callable:
    def search_fertilizer_info(query: str) -> dict:
        """Search for fertilizer information including NPK composition, dosage, and application timing.

        Args:
            query: Search query string (e.g. 'BioGrow fertilizante bonsai composicion NPK dosis').

        Returns:
            A dict with 'answer' (str summary) and 'results' (list of dicts with 'url' and 'content').
        """
        return searcher(query)

    return search_fertilizer_info


def _create_set_recommended_amount_tool(captured: dict) -> Callable:
    def set_recommended_amount(amount: str) -> dict:
        """Store the recommended dosage amount extracted from research.

        Call this once with the most concise dosage found (e.g. '5 ml/L', '2 g por litro').

        Args:
            amount: The recommended dosage as a short string.

        Returns:
            A dict with status 'success'.
        """
        captured["recommended_amount"] = amount
        return {"status": "success"}

    return set_recommended_amount


def _build_compile_prompt(name: str, relative_path: str, existing_content: str | None, user_instructions: str) -> str:
    parts = [f"Investiga y escribe la ficha wiki para el fertilizante {name}. Guárdala en la ruta: {relative_path}"]
    if existing_content:
        parts.append(f"\nContenido actual de la página:\n{existing_content}")
    if user_instructions:
        parts.append(f"\nInstrucciones específicas del usuario: {user_instructions}")
    return "\n".join(parts)


def _read_existing_page(path: Path) -> str | None:
    return path.read_text(encoding="utf-8") if path.exists() else None


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
