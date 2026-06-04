from typing import Callable

from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.fertilizer import Fertilizer
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


async def execute_create_fertilizer(
    name: str,
    get_fertilizer_by_name_func: Callable,
    wiki_page_builder: Callable,
    create_fertilizer_func: Callable,
    ask_confirmation: Callable,
    build_confirmation_message: Callable,
    user_id: str | None = None,
    tool_context=None,
) -> dict:
    """Core fertilizer creation logic shared by the ADK tool and direct Telegram commands."""
    if get_fertilizer_by_name_func(name):
        return {"status": "error", "message": "fertilizer_already_exists"}

    confirmed = await ask_confirmation(
        build_confirmation_message(name),
        user_id=user_id,
        tool_context=tool_context,
    )
    if confirmed:
        wiki_path, recommended_amount = await wiki_page_builder(name)
        create_fertilizer_func(
            fertilizer=Fertilizer(
                name=name,
                wiki_path=wiki_path,
                recommended_amount=recommended_amount,
            )
        )
        return {"status": "success", "message": f"Fertilizer '{name}' created."}

    return {"status": "cancelled", "reason": confirmed.reason}


def create_create_fertilizer_tool(
    create_fertilizer_func: Callable,
    get_fertilizer_by_name_func: Callable[[str], Fertilizer | None],
    wiki_page_builder: Callable[[str], tuple[str, str]],
    ask_confirmation: Callable,
    build_confirmation_message: Callable,
):
    @trace_tool_call
    @limit_tool_calls(agent_name="storekeeper")
    async def create_fertilizer(
        name: str,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Register a new fertilizer and generate its wiki page after user confirmation.

        Compiles a full technical wiki page (NPK composition, dosage, application timing)
        and stores the recommended amount extracted by the compiler agent.

        Args:
            name: Fertilizer name.

        Returns:
            A JSON-ready dictionary with status 'success', 'cancelled', or 'error'.
            Output JSON (success): {"status": "success", "message": "<confirmation>"}.
            Output JSON (cancelled): {"status": "cancelled", "message": "<reason>"}.
            Output JSON (error): {"status": "error", "message": "<reason>"}.
            Error reasons: "fertilizer_name_required", "fertilizer_already_exists".
        """
        if not name:
            return {"status": "error", "message": "fertilizer_name_required"}

        return await execute_create_fertilizer(
            name=name,
            get_fertilizer_by_name_func=get_fertilizer_by_name_func,
            wiki_page_builder=wiki_page_builder,
            create_fertilizer_func=create_fertilizer_func,
            ask_confirmation=ask_confirmation,
            build_confirmation_message=build_confirmation_message,
            tool_context=tool_context,
        )

    return create_fertilizer
