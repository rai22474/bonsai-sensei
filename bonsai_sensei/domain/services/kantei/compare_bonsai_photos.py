from typing import Callable

from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_compare_bonsai_photos_tool(
    get_bonsai_by_name_func: Callable,
    list_bonsai_photos_func: Callable,
    load_photo_bytes: Callable,
    run_photo_comparison: Callable,
) -> Callable:
    @trace_tool_call
    @limit_tool_calls(agent_name="kantei")
    async def compare_bonsai_photos(
        bonsai_name: str,
        comparison_intent: str = "",
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Compare two stored photos of a bonsai to track visual progress over time.

        Selects the oldest and newest stored photos, runs a visual comparison
        oriented to the given intent and returns the result.

        Args:
            bonsai_name: Name of the bonsai.
            comparison_intent: What to focus on when comparing, in the user's own words
                               (e.g. "cambios de salud", "evolución del diseño", "progreso general").
                               Leave empty for a general comparison.

        Returns:
            JSON dict with status 'comparison_complete', 'only_one_photo', 'no_photos', or 'error'.
            Output JSON (comparison_complete): {"status": "comparison_complete", "bonsai_name": str,
                "older_taken_on": "YYYY-MM-DD", "newer_taken_on": "YYYY-MM-DD", "comparison": str}.
            Output JSON (only_one_photo): {"status": "only_one_photo", "bonsai_name": str,
                "taken_on": "YYYY-MM-DD"}.
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

        if len(photos) == 1:
            return {
                "status": "only_one_photo",
                "bonsai_name": bonsai_name,
                "taken_on": str(photos[0].taken_on),
            }

        sorted_photos = sorted(photos, key=lambda photo: photo.taken_on)
        older_photo = sorted_photos[0]
        newer_photo = sorted_photos[-1]

        older_bytes = load_photo_bytes(older_photo.file_path)
        if older_bytes is None:
            return {"status": "error", "message": "photo_file_not_found"}

        newer_bytes = load_photo_bytes(newer_photo.file_path)
        if newer_bytes is None:
            return {"status": "error", "message": "photo_file_not_found"}

        comparison = await run_photo_comparison(older_bytes, newer_bytes, comparison_intent)

        if tool_context is not None:
            analyzed = list(tool_context.state.get("photos_for_analysis_taken_on") or [])
            analyzed.append(str(older_photo.taken_on))
            analyzed.append(str(newer_photo.taken_on))
            tool_context.state["photos_for_analysis_taken_on"] = analyzed

        return {
            "status": "comparison_complete",
            "bonsai_name": bonsai_name,
            "older_taken_on": str(older_photo.taken_on),
            "newer_taken_on": str(newer_photo.taken_on),
            "comparison": comparison,
        }

    return compare_bonsai_photos
