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

_APP_NAME = "phytosanitary_wiki_compiler"
_MAX_LLM_CALLS = 20

_COMPILER_INSTRUCTION = """
Eres un compilador de fichas técnicas de productos fitosanitarios para bonsáis. Dado el nombre de un producto, tu tarea es investigar su ficha técnica y escribir una página wiki completa en markdown en castellano.

# Comportamiento
- Usa search_phytosanitary_info para buscar: composición, modo de acción, dosis de uso, plagas objetivo, precauciones y fuentes.
- Escribe la ficha con write_wiki_page cuando tengas suficiente información. Solo debes llamar a write_wiki_page una vez.
- Llama a set_recommended_amount con la dosis de uso más concisa que hayas encontrado, expresada SIEMPRE en unidades métricas (e.g. "2 ml/L", "5 g por litro"). Si la fuente indica una medida informal, conviértela a mililitros. DEBES llamar a esta herramienta antes de terminar.
- Usa wikilinks [[../diseases/<slug>.md]] si el producto trata enfermedades o plagas específicas identificables. Sustituye <slug> por el nombre de la enfermedad en minúsculas con guiones.
- Incluye las URLs de las fuentes consultadas en una sección ## Fuentes al final.

# Formato de la ficha
La ficha debe contener las secciones: nombre del producto como título H1, párrafo introductorio, Composición activa, Dosis recomendada, Aplicación, Plagas y enfermedades objetivo, Precauciones y Fuentes.
"""

_COMPILE_PROMPT = "Investiga y escribe la ficha wiki para el fitosanitario {name}. Guárdala en la ruta: {relative_path}"


def create_phytosanitary_wiki_compiler(
    model: object,
    wiki_root: str | Path,
    searcher: Callable[[str], dict],
) -> Callable[[str], tuple[str, str]]:
    """Create an async compiler that generates a markdown wiki page for a phytosanitary product.

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

    async def compile_phytosanitary_page(name: str) -> tuple[str, str]:
        slug = _slugify(name)
        relative_path = f"phytosanitaries/{slug}.md"
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
        prompt = _COMPILE_PROMPT.format(name=name, relative_path=relative_path)
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

    return compile_phytosanitary_page


def _create_search_tool(searcher: Callable[[str], dict]) -> Callable:
    def search_phytosanitary_info(query: str) -> dict:
        """Search for phytosanitary product information including usage, dosage, and target pests.

        Args:
            query: Search query string (e.g. 'Neem Oil bonsai dosis fitosanitario').

        Returns:
            A dict with 'answer' (str summary) and 'results' (list of dicts with 'url' and 'content').
        """
        return searcher(query)

    return search_phytosanitary_info


def _create_set_recommended_amount_tool(captured: dict) -> Callable:
    def set_recommended_amount(amount: str) -> dict:
        """Store the recommended dosage amount extracted from research.

        Call this once with the most concise dosage found (e.g. '2 ml/L', '5 g por litro').

        Args:
            amount: The recommended dosage as a short string.

        Returns:
            A dict with status 'success'.
        """
        captured["recommended_amount"] = amount
        return {"status": "success"}

    return set_recommended_amount


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
