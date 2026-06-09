from pathlib import Path
from typing import Callable

from bonsai_sensei.domain.fertilization_plan import FertilizationPlan
from bonsai_sensei.domain.services.cultivation.plan.manage_plan import create_manage_plan_tool

_DOCSTRING = """Create or replace the fertilization plan for a bonsai for a given period. Runs a multi-turn clarification dialogue with the user before generating the plan, then asks for confirmation before persisting. If an active plan already exists, abandons it first.

Args:
    bonsai_name: Name of the bonsai to plan fertilization for.
    start_date: Start of the planning period in ISO format (YYYY-MM-DD).
    end_date: End of the planning period in ISO format (YYYY-MM-DD).

Returns:
    A JSON-ready dictionary with status 'success', 'cancelled', or 'error'.
    Output JSON (success): {"status": "success", "plan_id": int}.
    Output JSON (cancelled): {"status": "cancelled", "reason": str}.
    Output JSON (error): {"status": "error", "message": str}.
    Error messages: "bonsai_not_found", "no_fertilizers_available", "invalid_date_format".
"""

_TEMPLATE_DIR = Path(__file__).parent / "templates"


def create_manage_fertilization_plan_tool(
    get_bonsai_by_name_func: Callable,
    list_bonsai_events_func: Callable,
    list_fertilizers_func: Callable,
    get_fertilizer_by_name_func: Callable,
    get_active_fertilization_plan_func: Callable,
    create_fertilization_plan_func: Callable,
    update_fertilization_plan_func: Callable,
    create_planned_work_func: Callable,
    delete_future_planned_works_func: Callable,
    read_wiki_page_func: Callable,
    write_wiki_page_func: Callable,
    list_wiki_files_func: Callable,
    run_clarification_loop: Callable,
    run_plan_proposal: Callable,
    ask_human: Callable,
    build_bonsai_name_question: Callable,
) -> Callable:
    return create_manage_plan_tool(
        tool_name="manage_fertilization_plan",
        tool_docstring=_DOCSTRING,
        plan_class=FertilizationPlan,
        no_products_error="no_fertilizers_available",
        wiki_path_prefix="plans",
        plan_id_kwarg="plan_id",
        work_type="fertilizer_application",
        product_id_key="fertilizer_id",
        product_name_key="fertilizer_name",
        product_response_label="fertilizer",
        template_dir=_TEMPLATE_DIR,
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_bonsai_events_func=list_bonsai_events_func,
        list_products_func=list_fertilizers_func,
        get_product_by_name_func=get_fertilizer_by_name_func,
        get_active_plan_func=get_active_fertilization_plan_func,
        create_plan_func=create_fertilization_plan_func,
        update_plan_func=update_fertilization_plan_func,
        create_planned_work_func=create_planned_work_func,
        delete_future_planned_works_func=delete_future_planned_works_func,
        read_wiki_page_func=read_wiki_page_func,
        write_wiki_page_func=write_wiki_page_func,
        list_wiki_files_func=list_wiki_files_func,
        run_clarification_loop=run_clarification_loop,
        run_plan_proposal=run_plan_proposal,
        ask_human=ask_human,
        build_bonsai_name_question=build_bonsai_name_question,
    )
