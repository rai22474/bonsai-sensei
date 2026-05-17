import os
from functools import partial
from pathlib import Path

from bonsai_sensei.domain import bonsai_photo_store
from bonsai_sensei.domain import garden
from bonsai_sensei.domain.services.garden.kantei.analyze_bonsai_photo import create_analyze_bonsai_photo_tool
from bonsai_sensei.domain.services.garden.kantei.compare_bonsai_photos import create_compare_bonsai_photos_tool
from bonsai_sensei.domain.services.garden.kantei.kantei import create_kantei
from bonsai_sensei.domain.services.garden.kantei.photo_analysis_runner import create_photo_analysis_runner
from bonsai_sensei.domain.services.garden.kantei.photo_comparison_runner import create_photo_comparison_runner
from bonsai_sensei.domain.services.garden.kantei.update_reports_index import create_update_bonsai_reports_index_tool
from bonsai_sensei.domain.services.wiki_page import create_write_wiki_page_tool, create_list_wiki_files_tool


def create_kantei_group(model: object, session_factory) -> object:
    get_bonsai_by_name_func = partial(garden.get_bonsai_by_name, create_session=session_factory)
    list_bonsai_photos_func = partial(bonsai_photo_store.list_bonsai_photos, create_session=session_factory)
    photos_root = Path(os.getenv("PHOTOS_PATH", "./photos"))

    def load_photo_bytes(file_path: str) -> bytes | None:
        full_path = photos_root / file_path
        if not full_path.exists():
            return None
        return full_path.read_bytes()

    wiki_root = os.getenv("WIKI_PATH", "./wiki")
    write_wiki_page_tool = create_write_wiki_page_tool(wiki_root=wiki_root)
    list_wiki_files_func = create_list_wiki_files_tool(wiki_root=wiki_root)
    update_reports_index_tool = create_update_bonsai_reports_index_tool(
        list_wiki_files_func=list_wiki_files_func,
        write_wiki_page_func=write_wiki_page_tool,
    )

    run_photo_analysis = create_photo_analysis_runner(model)
    run_photo_comparison = create_photo_comparison_runner(model)

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

    return create_kantei(
        model=model,
        analyze_bonsai_photo_tool=analyze_tool,
        compare_bonsai_photos_tool=compare_tool,
    )
