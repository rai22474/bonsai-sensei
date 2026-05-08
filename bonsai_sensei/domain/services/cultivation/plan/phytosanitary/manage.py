from pathlib import Path
from typing import Callable

from bonsai_sensei.domain.phytosanitary_plan import PhytosanitaryPlan
from bonsai_sensei.domain.services.cultivation.plan.manage_plan import create_manage_plan_tool

_DOCSTRING = """Create or replace the phytosanitary protection plan for a bonsai for a given period. Runs a multi-turn clarification dialogue with the user before generating the plan, then asks for confirmation before persisting. If an active plan already exists, abandons it first.

Args:
    bonsai_name: Name of the bonsai to plan phytosanitary treatments for.
    start_date: Start of the planning period in ISO format (YYYY-MM-DD).
    end_date: End of the planning period in ISO format (YYYY-MM-DD).

Returns:
    A JSON-ready dictionary with status 'success', 'cancelled', or 'error'.
    Output JSON (success): {"status": "success", "plan_id": int}.
    Output JSON (cancelled): {"status": "cancelled", "reason": str}.
    Output JSON (error): {"status": "error", "message": str}.
    Error messages: "bonsai_not_found", "no_products_available", "invalid_date_format".
"""

_TEMPLATE_DIR = Path(__file__).parent / "templates"


def create_manage_phytosanitary_plan_tool(
    get_bonsai_by_name_func: Callable,
    list_bonsai_events_func: Callable,
    list_phytosanitary_func: Callable,
    get_phytosanitary_by_name_func: Callable,
    get_active_phytosanitary_plan_func: Callable,
    create_phytosanitary_plan_func: Callable,
    update_phytosanitary_plan_func: Callable,
    create_planned_work_func: Callable,
    delete_future_planned_works_func: Callable,
    read_wiki_page_func: Callable,
    write_wiki_page_func: Callable,
    list_wiki_files_func: Callable,
    run_clarification_loop: Callable,
    run_plan_proposal: Callable,
) -> Callable:
    return create_manage_plan_tool(
        tool_name="manage_phytosanitary_plan",
        tool_docstring=_DOCSTRING,
        plan_class=PhytosanitaryPlan,
        no_products_error="no_products_available",
        wiki_path_prefix="phytosanitary-plans",
        plan_id_kwarg="phytosanitary_plan_id",
        work_type="phytosanitary_application",
        product_id_key="phytosanitary_id",
        product_name_key="phytosanitary_name",
        product_response_label="product",
        template_dir=_TEMPLATE_DIR,
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_bonsai_events_func=list_bonsai_events_func,
        list_products_func=list_phytosanitary_func,
        get_product_by_name_func=get_phytosanitary_by_name_func,
        get_active_plan_func=get_active_phytosanitary_plan_func,
        create_plan_func=create_phytosanitary_plan_func,
        update_plan_func=update_phytosanitary_plan_func,
        create_planned_work_func=create_planned_work_func,
        delete_future_planned_works_func=delete_future_planned_works_func,
        read_wiki_page_func=read_wiki_page_func,
        write_wiki_page_func=write_wiki_page_func,
        list_wiki_files_func=list_wiki_files_func,
        run_clarification_loop=run_clarification_loop,
        run_plan_proposal=run_plan_proposal,
    )
