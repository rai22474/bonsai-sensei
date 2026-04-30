import os
from pathlib import Path
from typing import Callable

from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.services.human_input import SelectionNoneResult
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_delete_bonsai_photo_tool(
    get_bonsai_by_name_func: Callable,
    list_bonsai_photos_func: Callable,
    delete_bonsai_photo_func: Callable,
    ask_confirmation: Callable,
    ask_selection: Callable,
    build_selection_question: Callable,
    build_confirmation_message: Callable,
) -> Callable:
    photos_root = Path(os.getenv("PHOTOS_PATH", "./photos"))

    @trace_tool_call
    @limit_tool_calls(agent_name="gardener")
    async def delete_bonsai_photo(
        bonsai_name: str,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Delete a stored photo from a bonsai.

        Call this directly with just the bonsai name — do not ask the user which photo
        to delete beforehand. This tool handles showing available photos, user selection,
        and deletion confirmation internally.

        Args:
            bonsai_name: Name of the bonsai whose photo should be deleted.

        Returns:
            A JSON-ready dictionary with status 'success', 'cancelled', or 'error'.
            Output JSON (success): {"status": "success", "message": "<confirmation>"}.
            Output JSON (cancelled): {"status": "cancelled", "reason": "<reason>"}.
            Output JSON (error): {"status": "error", "message": "<reason>"}.
            Error reasons: "bonsai_not_found", "no_photos_available".
        """
        bonsai = get_bonsai_by_name_func(bonsai_name)
        if not bonsai:
            return {"status": "error", "message": "bonsai_not_found"}

        photos = list_bonsai_photos_func(bonsai_id=bonsai.id)
        if not photos:
            return {"status": "error", "message": "no_photos_available"}

        options = [
            f"Foto del {photo.taken_on}" for photo in photos
        ]
        photo_paths = [photo.file_path for photo in photos]

        selection = await ask_selection(
            build_selection_question(bonsai_name),
            options,
            tool_context=tool_context,
            photos=photo_paths,
        )
        if isinstance(selection, SelectionNoneResult):
            return {"status": "cancelled", "reason": selection.reason}

        selected_index = options.index(selection) if selection in options else -1
        if selected_index == -1:
            return {"status": "error", "message": "invalid_selection"}

        selected_photo = photos[selected_index]
        confirmed = await ask_confirmation(
            build_confirmation_message(bonsai_name, str(selected_photo.taken_on)),
            tool_context=tool_context,
        )
        if not confirmed:
            return {"status": "cancelled", "reason": confirmed.reason}

        delete_bonsai_photo_func(photo_id=selected_photo.id)

        photo_file = photos_root / selected_photo.file_path
        if photo_file.exists():
            photo_file.unlink()

        return {"status": "success", "message": f"Photo from {selected_photo.taken_on} deleted for bonsai '{bonsai_name}'."}

    return delete_bonsai_photo
