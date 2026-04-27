from typing import Callable

from google.adk.tools.tool_context import ToolContext


def create_list_bonsai_photos_tool(
    get_bonsai_by_name_func: Callable,
    list_bonsai_photos_func: Callable,
    set_photos_for_display: bool = False,
) -> Callable:
    async def list_bonsai_photos(
        bonsai_name: str,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """List all photos registered for a bonsai, ordered by date ascending.

        Args:
            bonsai_name: Name of the bonsai.

        Returns:
            JSON with status 'success' or 'error'.
            Output JSON (success): {"status": "success", "photos": [{"id": int, "file_path": str, "taken_on": "YYYY-MM-DD"}, ...]}.
            Output JSON (error): {"status": "error", "message": "bonsai_not_found"}.
        """
        bonsai = get_bonsai_by_name_func(bonsai_name)
        if not bonsai:
            return {"status": "error", "message": "bonsai_not_found"}
        photos = list_bonsai_photos_func(bonsai_id=bonsai.id)
        if set_photos_for_display and tool_context is not None:
            tool_context.state["photos_to_display"] = [photo.file_path for photo in photos]
        return {
            "status": "success",
            "photos": [
                {"id": photo.id, "file_path": photo.file_path, "taken_on": str(photo.taken_on)}
                for photo in photos
            ],
        }

    return list_bonsai_photos
