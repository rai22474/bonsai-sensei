from typing import Callable

from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.bonsai_event import BonsaiEvent
from bonsai_sensei.domain.services.human_input import SelectionNoneResult
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_create_pest_event_tool(
    get_bonsai_by_name_func: Callable,
    get_pest_by_name_func: Callable,
    list_phytosanitary_func: Callable,
    get_phytosanitary_by_name_func: Callable,
    record_bonsai_event_func: Callable,
    get_active_phytosanitary_plan_func: Callable,
    ask_confirmation: Callable,
    ask_selection: Callable,
    ask_plan_review: Callable,
    build_confirmation_message: Callable,
    build_applied_treatment_question: Callable,
    build_treatment_selection_question: Callable,
    build_plan_review_proposal: Callable,
) -> Callable:
    @trace_tool_call
    @limit_tool_calls(agent_name="caretaker")
    async def create_pest_event(
        bonsai_name: str,
        pest_name: str,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Record a pest detection event on a bonsai. Use this tool for ALL pest detections.

        After confirming the pest event, the tool interactively asks the user whether they also
        applied a phytosanitary treatment and handles the treatment recording internally, linking
        it to the pest event. It also checks for active phytosanitary plans and proposes a review
        if one exists.

        Args:
            bonsai_name: Name of the bonsai where the pest was detected.
            pest_name: Name of the pest detected (must be registered in the catalog).

        Returns:
            A JSON-ready dictionary with status 'success', 'cancelled', or 'error'.
            Output JSON (success): {"status": "success", "pest_event_id": <id>, "message": "<confirmation>"}.
            Output JSON (cancelled): {"status": "cancelled", "reason": "<reason>"}.
            Output JSON (error): {"status": "error", "message": "<reason>"}.
            Error reasons: "bonsai_name_required", "pest_name_required",
                "bonsai_not_found", "pest_not_found".
        """
        if not bonsai_name:
            return {"status": "error", "message": "bonsai_name_required"}

        if not pest_name:
            return {"status": "error", "message": "pest_name_required"}

        bonsai = get_bonsai_by_name_func(bonsai_name)
        if not bonsai:
            return {"status": "error", "message": "bonsai_not_found"}

        pest = get_pest_by_name_func(pest_name)
        if not pest:
            return {"status": "error", "message": "pest_not_found"}

        confirmed = await ask_confirmation(
            build_confirmation_message(bonsai_name, pest_name),
            tool_context=tool_context,
        )
        if not confirmed:
            return {"status": "cancelled", "reason": confirmed.reason}

        selected_phytosanitary = await _resolve_applied_phytosanitary(
            bonsai_name=bonsai_name,
            pest_name=pest_name,
            list_phytosanitary_func=list_phytosanitary_func,
            get_phytosanitary_by_name_func=get_phytosanitary_by_name_func,
            ask_confirmation=ask_confirmation,
            ask_selection=ask_selection,
            build_applied_treatment_question=build_applied_treatment_question,
            build_treatment_selection_question=build_treatment_selection_question,
            tool_context=tool_context,
        )

        pest_event = _record_pest_with_optional_treatment(
            bonsai_id=bonsai.id,
            pest_id=pest.id,
            pest_name=pest_name,
            phytosanitary=selected_phytosanitary,
            record_bonsai_event_func=record_bonsai_event_func,
        )

        active_plan = get_active_phytosanitary_plan_func(bonsai_id=bonsai.id)
        if active_plan:
            await ask_plan_review(
                build_plan_review_proposal(bonsai_name, pest_name),
                tool_context=tool_context,
            )

        return {
            "status": "success",
            "pest_event_id": pest_event.id,
            "message": f"Pest detection of '{pest_name}' recorded on '{bonsai_name}'.",
        }

    return create_pest_event


async def _resolve_applied_phytosanitary(
    bonsai_name: str,
    pest_name: str,
    list_phytosanitary_func: Callable,
    get_phytosanitary_by_name_func: Callable,
    ask_confirmation: Callable,
    ask_selection: Callable,
    build_applied_treatment_question: Callable,
    build_treatment_selection_question: Callable,
    tool_context,
):
    product_names = [product.name for product in list_phytosanitary_func()]
    if not product_names:
        return None
    treatment_applied = await ask_confirmation(
        build_applied_treatment_question(bonsai_name, pest_name),
        tool_context=tool_context,
    )
    if not treatment_applied:
        return None
    selected_product_name = await ask_selection(
        build_treatment_selection_question(),
        options=product_names,
        tool_context=tool_context,
    )
    if selected_product_name and not isinstance(selected_product_name, SelectionNoneResult):
        return get_phytosanitary_by_name_func(selected_product_name)
    return None


def _record_pest_with_optional_treatment(
    bonsai_id: int,
    pest_id: int,
    pest_name: str,
    phytosanitary,
    record_bonsai_event_func: Callable,
):
    pest_event = record_bonsai_event_func(
        bonsai_event=BonsaiEvent(
            bonsai_id=bonsai_id,
            event_type="pest_detection",
            payload={"pest_id": pest_id, "pest_name": pest_name},
        )
    )
    if phytosanitary:
        record_bonsai_event_func(
            bonsai_event=BonsaiEvent(
                bonsai_id=bonsai_id,
                event_type="phytosanitary_application",
                payload={
                    "phytosanitary_id": phytosanitary.id,
                    "phytosanitary_name": phytosanitary.name,
                    "pest_event_id": pest_event.id,
                },
            )
        )
    return pest_event
