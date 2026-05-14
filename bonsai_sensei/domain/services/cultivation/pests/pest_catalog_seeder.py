import logging
import uuid
from typing import Callable

from google.adk.agents.llm_agent import Agent
from google.adk.runners import InMemoryRunner, RunConfig
from google.genai import types

from bonsai_sensei.domain.pest import Pest

_APP_NAME = "pest_catalog_seeder"
_MAX_LLM_CALLS = 30
_logger = logging.getLogger(__name__)

_SEEDER_INSTRUCTION = """
Eres un asistente que identifica y registra las plagas más comunes para una especie de bonsái.

# Comportamiento
- Usa search_pest_info para buscar las plagas más comunes que afectan a bonsáis de la especie indicada.
- Identifica entre 3 y 6 plagas distintas y representativas.
- Para cada plaga identificada, llama a register_pest con el nombre de la plaga en español y en minúsculas.
- No registres la misma plaga dos veces.
- Termina cuando hayas registrado todas las plagas identificadas.
"""


def create_pest_catalog_seeder(
    model: object,
    searcher: Callable[[str], dict],
    compile_pest_page: Callable[[str, str], str],
    create_pest_func: Callable,
    get_pest_by_name_func: Callable,
) -> Callable[[str], None]:
    """Create an async function that seeds the pest catalog for a newly created species.

    Runs a dedicated ADK agent that searches for common pests of the species and
    registers each one via compile_pest_page + create_pest_func.

    Args:
        model: LLM model to use for the seeder agent.
        searcher: Callable that accepts a search query and returns a Tavily-like dict.
        compile_pest_page: Async callable that generates a wiki page for a pest.
        create_pest_func: Callable that persists a Pest entity.
        get_pest_by_name_func: Callable that looks up a pest by name.
    """
    search_tool = _create_search_tool(searcher)

    async def seed_pest_catalog(species_name: str) -> None:
        registered: list[str] = []

        def register_pest(pest_name: str) -> dict:
            """Register a pest in the catalog and generate its wiki page.

            Args:
                pest_name: Name of the pest in Spanish, lowercase (e.g. 'araña roja').

            Returns:
                A dict with 'status' 'success' or 'already_exists'.
            """
            if get_pest_by_name_func(name=pest_name):
                return {"status": "already_exists", "pest_name": pest_name}
            registered.append(pest_name)
            return {"status": "success", "pest_name": pest_name}

        agent = Agent(
            model=model,
            name=_APP_NAME,
            instruction=_SEEDER_INSTRUCTION,
            tools=[search_tool, register_pest],
        )
        runner = InMemoryRunner(agent=agent, app_name=_APP_NAME)
        session_id = str(uuid.uuid4())
        await runner.session_service.create_session(
            app_name=_APP_NAME,
            user_id=_APP_NAME,
            session_id=session_id,
        )
        prompt = f"Identifica y registra las plagas más comunes de bonsáis de especie {species_name}."
        message = types.Content(role="user", parts=[types.Part(text=prompt)])
        run_config = RunConfig(max_llm_calls=_MAX_LLM_CALLS)
        async for _ in runner.run_async(
            user_id=_APP_NAME,
            session_id=session_id,
            new_message=message,
            run_config=run_config,
        ):
            pass

        for pest_name in registered:
            try:
                wiki_path = await compile_pest_page(pest_name)
                create_pest_func(pest=Pest(name=pest_name, wiki_path=wiki_path))
            except Exception:
                _logger.exception("Failed to register pest '%s' for species '%s'", pest_name, species_name)

    return seed_pest_catalog


def _create_search_tool(searcher: Callable[[str], dict]) -> Callable:
    def search_pest_info(query: str) -> dict:
        """Search for information about pests affecting a bonsai species.

        Args:
            query: Search query (e.g. 'plagas comunes bonsái Ficus retusa').

        Returns:
            A dict with 'answer' (str summary) and 'results' (list of dicts with 'url' and 'content').
        """
        return searcher(query)

    return search_pest_info
