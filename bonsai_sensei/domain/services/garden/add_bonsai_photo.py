from typing import Callable

from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.bonsai_photo import BonsaiPhoto
from bonsai_sensei.domain.services.human_input import SelectionNoneResult
from bonsai_sensei.domain.services.resolve_user_id import resolve_confirmation_user_id
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_add_bonsai_photo_tool(
    get_bonsai_by_name_func: Callable,
    list_bonsai_func: Callable,
    create_bonsai_photo_func: Callable,
    ask_confirmation: Callable,
    ask_selection: Callable,
    build_selection_question: Callable,
    build_confirmation_message: Callable,
    get_pending_photo_bytes: Callable,
    save_photo_file: Callable,
    clear_pending_photo: Callable,
) -> Callable:
    @trace_tool_call
    @limit_tool_calls(agent_name="gardener")
    async def add_bonsai_photo(
        bonsai_name: str = "",
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Register the pending photo as belonging to a bonsai after user selects which bonsai and confirms.

        The photo has already been received and is stored pending assignment. Call this tool
        immediately when a photo is visible in the conversation — do not ask the user which
        bonsai before calling; the tool handles that interaction.

        Args:
            bonsai_name: Optional name of the bonsai. If empty, user selects from a list.

        Returns:
            A JSON-ready dictionary with status 'success', 'cancelled', or 'error'.
            Output JSON (success): {"status": "success", "message": "<confirmation>"}.
            Output JSON (cancelled): {"status": "cancelled", "reason": "<reason>"}.
            Output JSON (error): {"status": "error", "message": "<reason>"}.
            Error reasons: "no_pending_photo", "no_bonsai_available", "bonsai_not_found".
        """
        user_id = resolve_confirmation_user_id(tool_context)
        photo_bytes = get_pending_photo_bytes(user_id)
        if not photo_bytes:
            return {"status": "error", "message": "no_pending_photo"}

        if not bonsai_name:
            all_bonsai = list_bonsai_func()
            if not all_bonsai:
                return {"status": "error", "message": "no_bonsai_available"}
            bonsai_names = [bonsai.name for bonsai in all_bonsai]
            selection = await ask_selection(
                build_selection_question(),
                bonsai_names,
                tool_context=tool_context,
            )
            if isinstance(selection, SelectionNoneResult):
                clear_pending_photo(user_id)
                return {"status": "cancelled", "reason": selection.reason}
            bonsai_name = selection

        bonsai = get_bonsai_by_name_func(bonsai_name)
        if not bonsai:
            return {"status": "error", "message": "bonsai_not_found"}

        confirmed = await ask_confirmation(
            build_confirmation_message(bonsai_name), tool_context=tool_context
        )

        if confirmed:
            file_path = save_photo_file(bonsai_name, photo_bytes)
            create_bonsai_photo_func(
                bonsai_photo=BonsaiPhoto(bonsai_id=bonsai.id, file_path=file_path)
            )
            clear_pending_photo(user_id)
            return {"status": "success", "message": f"Photo registered for bonsai '{bonsai_name}'."}

        clear_pending_photo(user_id)
        return {"status": "cancelled", "reason": confirmed.reason}

    return add_bonsai_photo
