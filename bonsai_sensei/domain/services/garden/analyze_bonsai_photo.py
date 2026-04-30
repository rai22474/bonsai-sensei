from typing import Callable

from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_analyze_bonsai_photo_tool(
    get_bonsai_by_name_func: Callable,
    list_bonsai_photos_func: Callable,
    load_photo_bytes: Callable,
) -> Callable:
    @trace_tool_call
    @limit_tool_calls(agent_name="gardener")
    async def analyze_bonsai_photo(
        bonsai_name: str,
        date_hint: str = "",
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Retrieve a stored photo of the given bonsai and prepare it for visual analysis.

        Loads the photo from disk and makes it available so the next response can describe
        what is visible in it. Call this when the user asks for visual analysis, description,
        or critique of a bonsai based on a stored photo.

        Args:
            bonsai_name: Name of the bonsai.
            date_hint: Optional date hint in natural language (e.g. "enero", "2025-06-25").
                       Leave empty to use the latest photo.

        Returns:
            JSON dict with status 'photo_ready', 'no_photos', or 'error'.
            Output JSON (photo_ready): {"status": "photo_ready", "bonsai_name": str, "taken_on": "YYYY-MM-DD"}.
            Output JSON (no_photos): {"status": "no_photos", "bonsai_name": str}.
            Output JSON (error): {"status": "error", "message": str}.
            Error messages: "bonsai_not_found", "photo_file_not_found".
        """
        bonsai = get_bonsai_by_name_func(bonsai_name)
        if not bonsai:
            return {"status": "error", "message": "bonsai_not_found"}

        photos = list_bonsai_photos_func(bonsai_id=bonsai.id)
        if not photos:
            return {"status": "no_photos", "bonsai_name": bonsai_name}

        photo = _select_photo(photos, date_hint)
        photo_bytes = load_photo_bytes(photo.file_path)
        if photo_bytes is None:
            return {"status": "error", "message": "photo_file_not_found"}

        if tool_context is not None:
            tool_context.state["photo_for_analysis"] = photo_bytes

        return {
            "status": "photo_ready",
            "bonsai_name": bonsai_name,
            "taken_on": str(photo.taken_on),
        }

    return analyze_bonsai_photo


def _select_photo(photos: list, date_hint: str):
    if not date_hint:
        return photos[-1]
    return photos[-1]
