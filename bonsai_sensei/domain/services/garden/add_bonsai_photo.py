from typing import Callable

from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.bonsai_photo import BonsaiPhoto
from bonsai_sensei.domain.services.human_input import SelectionNoneResult
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
) -> Callable:
    @trace_tool_call
    @limit_tool_calls(agent_name="gardener")
    async def add_bonsai_photo(
        photo_path: str,
        bonsai_name: str = "",
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Register a photo as belonging to a bonsai after user selects which bonsai and confirms.

        When bonsai_name is not provided, presents a selection list of all available bonsais.
        Call this tool directly when a [FOTO RECIBIDA] marker is present — do not ask the user
        which bonsai before calling; the tool handles that interaction.

        Args:
            photo_path: Path to the photo file already saved on disk.
            bonsai_name: Optional name of the bonsai. If empty, user selects from a list.

        Returns:
            A JSON-ready dictionary with status 'success', 'cancelled', or 'error'.
            Output JSON (success): {"status": "success", "message": "<confirmation>"}.
            Output JSON (cancelled): {"status": "cancelled", "reason": "<reason>"}.
            Output JSON (error): {"status": "error", "message": "<reason>"}.
            Error reasons: "photo_path_required", "no_bonsai_available", "bonsai_not_found".
        """
        if not photo_path:
            return {"status": "error", "message": "photo_path_required"}

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
                return {"status": "cancelled", "reason": selection.reason}
            bonsai_name = selection

        bonsai = get_bonsai_by_name_func(bonsai_name)
        if not bonsai:
            return {"status": "error", "message": "bonsai_not_found"}

        confirmed = await ask_confirmation(
            build_confirmation_message(bonsai_name), tool_context=tool_context
        )

        if confirmed:
            create_bonsai_photo_func(
                bonsai_photo=BonsaiPhoto(bonsai_id=bonsai.id, file_path=photo_path)
            )
            return {"status": "success", "message": f"Photo registered for bonsai '{bonsai_name}'."}

        return {"status": "cancelled", "reason": confirmed.reason}

    return add_bonsai_photo
