from typing import Callable

from google.adk.tools.tool_context import ToolContext


def create_list_bonsai_photos_tool(
    get_bonsai_by_name_func: Callable,
    list_bonsai_photos_func: Callable,
) -> Callable:
    async def list_bonsai_photos(
        bonsai_name: str,
    ) -> dict:
        """Return the metadata (id, file_path, taken_on) of all registered photos for a bonsai, ordered by date ascending. Use this to answer questions about which photos a bonsai has or how many. Does NOT send the images to the user.

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
        return {
            "status": "success",
            "photos": [
                {"id": photo.id, "file_path": photo.file_path, "taken_on": str(photo.taken_on)}
                for photo in photos
            ],
        }

    return list_bonsai_photos


def create_show_bonsai_photos_tool(
    get_bonsai_by_name_func: Callable,
    list_bonsai_photos_func: Callable,
) -> Callable:
    async def show_bonsai_photos(
        bonsai_name: str,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Retrieve and display the photos of a bonsai. Use this only when the user explicitly asks to see, view, or show the photos. Sends the actual images to the user.

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
        if tool_context is not None:
            tool_context.state["photos_to_display"] = [photo.file_path for photo in photos]
        return {
            "status": "success",
            "photos": [
                {"id": photo.id, "file_path": photo.file_path, "taken_on": str(photo.taken_on)}
                for photo in photos
            ],
        }

    return show_bonsai_photos
