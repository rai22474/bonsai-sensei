import os
from functools import partial
from pathlib import Path
from typing import Callable

from bonsai_sensei.domain import bonsai_photo_store
from bonsai_sensei.domain import garden
from bonsai_sensei.domain.services.garden.kantei.analyze_bonsai_photo import create_analyze_bonsai_photo_tool
from bonsai_sensei.domain.services.garden.kantei.compare_bonsai_photos import create_compare_bonsai_photos_tool
from bonsai_sensei.domain.services.garden.kantei.photo_analysis_runner import create_photo_analysis_runner
from bonsai_sensei.domain.services.garden.kantei.photo_comparison_runner import create_photo_comparison_runner
from bonsai_sensei.domain.services.garden.kantei.update_reports_index import create_update_bonsai_reports_index_tool
from bonsai_sensei.infrastructure.wiki_client import (
    create_http_write_wiki_page_tool,
    create_http_list_wiki_files_tool,
    create_http_search_wiki_knowledge_tool,
)

ANALYZE_TOOL_DESCRIPTION = (
    "- analyze_bonsai_photo: Analiza visualmente una foto almacenada de un bonsái. "
    "Parámetros: bonsai_name (str), analysis_type ('health'|'design'|'general'), date_hint (str, opcional — mes en español o fecha YYYY-MM-DD)."
)
COMPARE_TOOL_DESCRIPTION = (
    "- compare_bonsai_photos: Compara la foto más antigua con la más reciente de un bonsái para ver su evolución. "
    "Parámetros: bonsai_name (str), comparison_intent (str, opcional — qué aspecto comparar)."
)


def create_kantei_group(model: object, session_factory, orchestrator_model: object = None, kb_base_url: str = "") -> tuple[Callable, Callable]:
    effective_orchestrator_model = orchestrator_model or model
    get_bonsai_by_name_func = partial(garden.get_bonsai_by_name, create_session=session_factory)
    list_bonsai_photos_func = partial(bonsai_photo_store.list_bonsai_photos, create_session=session_factory)
    photos_root = Path(os.getenv("PHOTOS_PATH", "./photos"))

    def load_photo_bytes(file_path: str) -> bytes | None:
        full_path = photos_root / file_path
        if not full_path.exists():
            return None
        return full_path.read_bytes()

    kb_base_url = os.getenv("KB_BASE_URL", "http://knowledge_base:8080")
    write_wiki_page_tool = create_http_write_wiki_page_tool(kb_base_url)
    list_wiki_files_func = create_http_list_wiki_files_tool(kb_base_url)
    update_reports_index_tool = create_update_bonsai_reports_index_tool(
        list_wiki_files_func=list_wiki_files_func,
        write_wiki_page_func=write_wiki_page_tool,
    )

    search_wiki_knowledge = create_http_search_wiki_knowledge_tool(kb_base_url) if kb_base_url else None
    run_photo_analysis = create_photo_analysis_runner(effective_orchestrator_model, search_wiki_knowledge=search_wiki_knowledge)
    run_photo_comparison = create_photo_comparison_runner(effective_orchestrator_model)

    analyze_tool = create_analyze_bonsai_photo_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_bonsai_photos_func=list_bonsai_photos_func,
        load_photo_bytes=load_photo_bytes,
        run_photo_analysis=run_photo_analysis,
        write_wiki_page_func=write_wiki_page_tool,
        update_reports_index_func=update_reports_index_tool,
    )
    analyze_tool.__name__ = "analyze_bonsai_photo"

    compare_tool = create_compare_bonsai_photos_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_bonsai_photos_func=list_bonsai_photos_func,
        load_photo_bytes=load_photo_bytes,
        run_photo_comparison=run_photo_comparison,
        write_wiki_page_func=write_wiki_page_tool,
        update_reports_index_func=update_reports_index_tool,
    )
    compare_tool.__name__ = "compare_bonsai_photos"

    return analyze_tool, compare_tool
