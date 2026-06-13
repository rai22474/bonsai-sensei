import os
from functools import partial
from pathlib import Path
from typing import Callable

from google.adk.agents.llm_agent import LlmAgent
from google.genai import types

from bonsai_sensei.domain import cultivation_plan
from bonsai_sensei.domain import development_plan_store
from bonsai_sensei.domain import garden
from bonsai_sensei.domain.services.cultivation.plan.refinement.analyze_work_photo import create_analyze_work_photo_tool
from bonsai_sensei.domain.services.cultivation.plan.refinement.kiroku import create_kiroku
from bonsai_sensei.domain.services.cultivation.plan.refinement.save_work_notes import (
    WIKI_INSTRUCTION,
    create_close_work_session_tool,
    create_document_work_session_tool,
)
from bonsai_sensei.domain.services.cultivation.plan.refinement.start_work_documentation import create_start_work_documentation_tool
from bonsai_sensei.domain.services.extract_text_from_events import extract_text_from_events
from bonsai_sensei.domain.services.llm_runner import create_single_turn_llm_runner
from bonsai_sensei.domain.services.resolve_user_id import resolve_confirmation_user_id
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call
from bonsai_sensei.infrastructure.wiki_client import (
    create_http_read_wiki_page_tool,
    create_http_search_wiki_knowledge_tool,
    create_http_write_wiki_page_tool,
)


def create_kiroku_group(
    model: object,
    session_factory,
    ask_human: Callable,
    ask_selection: Callable,
    build_bonsai_name_question: Callable,
    build_work_selection_question: Callable,
    build_work_option_label: Callable,
    pending_photos: dict,
    orchestrator_model: object = None,
    search_memory_func: Callable | None = None,
) -> LlmAgent:
    effective_model = orchestrator_model or model
    kb_base_url = os.getenv("KB_BASE_URL", "http://knowledge_base:8080")
    read_wiki_page_func = create_http_read_wiki_page_tool(kb_base_url)
    write_wiki_page_func = create_http_write_wiki_page_tool(kb_base_url)
    photos_root = Path(os.getenv("PHOTOS_PATH", "./photos"))

    def get_pending_photo_bytes(user_id: str) -> bytes | None:
        return pending_photos.get(user_id)

    def clear_pending_photo(user_id: str) -> None:
        pending_photos.pop(user_id, None)

    def save_session_photo(user_id: str, work_id: int, session_date: str, photo_n: int, photo_bytes: bytes) -> None:
        session_dir = photos_root / "sessions" / user_id / f"{work_id}-{session_date}"
        session_dir.mkdir(parents=True, exist_ok=True)
        (session_dir / f"photo-{photo_n}.webp").write_bytes(photo_bytes)

    async def run_contextual_photo_analysis(photo_bytes: bytes, instruction: str) -> str:
        runner = create_single_turn_llm_runner(
            model=effective_model,
            app_name="kiroku_photo_analysis",
            instruction=instruction,
            max_llm_calls=4,
        )
        message = types.Content(
            role="user",
            parts=[types.Part(inline_data=types.Blob(mime_type="image/webp", data=photo_bytes))],
        )
        return await extract_text_from_events(runner(message))

    run_wiki_generator = create_single_turn_llm_runner(
        model=effective_model,
        app_name="kiroku_wiki",
        instruction=WIKI_INSTRUCTION,
        max_llm_calls=6,
    )
    update_wiki_paths_func = partial(cultivation_plan.update_planned_work_wiki_paths, create_session=session_factory)

    def update_refinement_wiki_path(work_id: int, wiki_path: str) -> None:
        update_wiki_paths_func(work_id=work_id, refinement_wiki_path=wiki_path)

    def update_result_wiki_path(work_id: int, wiki_path: str) -> None:
        update_wiki_paths_func(work_id=work_id, result_wiki_path=wiki_path)

    start_tool = create_start_work_documentation_tool(
        get_bonsai_by_name_func=partial(garden.get_bonsai_by_name, create_session=session_factory),
        list_planned_works_func=partial(cultivation_plan.list_planned_works, create_session=session_factory),
        ask_human=ask_human,
        ask_selection=ask_selection,
        build_bonsai_name_question=build_bonsai_name_question,
        build_work_selection_question=build_work_selection_question,
        build_work_option_label=build_work_option_label,
    )
    get_bonsai_by_id_func = partial(garden.get_bonsai_by_id, create_session=session_factory)
    get_planned_work_func = partial(cultivation_plan.get_planned_work, create_session=session_factory)

    analyze_tool = create_analyze_work_photo_tool(
        run_photo_analysis_func=run_contextual_photo_analysis,
        get_pending_photo_bytes=get_pending_photo_bytes,
        save_session_photo=save_session_photo,
        clear_pending_photo=clear_pending_photo,
        get_bonsai_by_id_func=get_bonsai_by_id_func,
        get_planned_work_func=get_planned_work_func,
    )
    document_session_tool = create_document_work_session_tool(
        run_wiki_generator=run_wiki_generator,
        get_planned_work_func=get_planned_work_func,
        get_bonsai_by_id_func=get_bonsai_by_id_func,
        read_wiki_page_func=read_wiki_page_func,
        write_wiki_page_func=write_wiki_page_func,
        get_development_plan_func=partial(development_plan_store.get_development_plan, create_session=session_factory),
        update_refinement_wiki_path_func=update_refinement_wiki_path,
        update_result_wiki_path_func=update_result_wiki_path,
        link_recent_photos_func=partial(cultivation_plan.link_recent_photos_to_work, create_session=session_factory),
    )
    close_session_tool = create_close_work_session_tool()
    search_wiki_tool = create_http_search_wiki_knowledge_tool(kb_base_url)
    load_memory_tool = _create_load_memory_tool(search_memory_func) if search_memory_func else None

    return create_kiroku(
        model=model,
        start_work_documentation_tool=start_tool,
        analyze_work_photo_tool=analyze_tool,
        document_work_session_tool=document_session_tool,
        close_work_session_tool=close_session_tool,
        search_wiki_tool=search_wiki_tool,
        load_memory_tool=load_memory_tool,
    )


def _create_load_memory_tool(search_memory_func: Callable) -> Callable:
    @trace_tool_call
    async def load_memory(query: str, tool_context=None) -> str:
        """Search episodic memory for past sessions and conversations relevant to the query.

        Use when the user references past sessions, or when context from previous work
        on this bonsai would enrich the current documentation or answer a question.

        Args:
            query: Semantic search query describing what to recall (e.g. 'mekiri Naruto resultados').
            tool_context: ADK tool context.
        """
        user_id = resolve_confirmation_user_id(tool_context)
        result = await search_memory_func(user_id=user_id, query=query)
        return result or "No se encontraron recuerdos relevantes."
    return load_memory
