from typing import Callable

from bonsai_sensei.domain.services.cultivation.plan.abandon_plan import create_abandon_plan_tool

_DOCSTRING = """Abandon the active phytosanitary plan for a bonsai after explicit user confirmation. Marks the plan as abandoned, records the reason, deletes all future scheduled treatments from this plan, and updates the wiki page.

Args:
    bonsai_name: Name of the bonsai whose active phytosanitary plan should be abandoned.
    reason: Explanation for why the plan is being abandoned.

Returns:
    A JSON-ready dictionary with status 'success', 'cancelled', or 'error'.
    Output JSON (success): {"status": "success", "plan_id": int}.
    Output JSON (cancelled): {"status": "cancelled", "reason": str}.
    Output JSON (error): {"status": "error", "message": "bonsai_not_found" | "no_active_plan"}.
"""


def create_abandon_phytosanitary_plan_tool(
    get_bonsai_by_name_func: Callable,
    get_active_phytosanitary_plan_func: Callable,
    update_phytosanitary_plan_func: Callable,
    delete_future_planned_works_func: Callable,
    read_wiki_page_func: Callable,
    write_wiki_page_func: Callable,
    ask_confirmation: Callable,
    build_confirmation_message: Callable,
) -> Callable:
    return create_abandon_plan_tool(
        tool_name="abandon_phytosanitary_plan",
        tool_docstring=_DOCSTRING,
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        get_active_plan_func=get_active_phytosanitary_plan_func,
        update_plan_func=update_phytosanitary_plan_func,
        delete_future_planned_works_func=delete_future_planned_works_func,
        read_wiki_page_func=read_wiki_page_func,
        write_wiki_page_func=write_wiki_page_func,
        ask_confirmation=ask_confirmation,
        build_confirmation_message=build_confirmation_message,
    )
