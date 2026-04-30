from datetime import date
from typing import Callable

from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call

_SPANISH_MONTHS = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}


def create_analyze_bonsai_photo_tool(
    get_bonsai_by_name_func: Callable,
    list_bonsai_photos_func: Callable,
    load_photo_bytes: Callable,
    run_photo_analysis: Callable,
) -> Callable:
    @trace_tool_call
    @limit_tool_calls(agent_name="kantei")
    async def analyze_bonsai_photo(
        bonsai_name: str,
        analysis_intent: str,
        date_hint: str = "",
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Retrieve a stored photo of the given bonsai and produce a visual analysis.

        Selects the photo matching the date hint (or the latest if omitted), runs the
        visual analysis oriented to the given intent and returns the result.

        Args:
            bonsai_name: Name of the bonsai.
            analysis_intent: What the user wants from the analysis, in the user's own words
                             (e.g. "diagnostica si tiene plagas", "critica el diseño",
                             "describe el estado general"). Used to orient the analysis.
            date_hint: Optional date hint in natural language (e.g. "enero", "2025-06-25").
                       Leave empty to use the latest photo.

        Returns:
            JSON dict with status 'analysis_complete', 'no_photos', or 'error'.
            Output JSON (analysis_complete): {"status": "analysis_complete", "bonsai_name": str, "taken_on": "YYYY-MM-DD", "analysis": str}.
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

        analysis = await run_photo_analysis(photo_bytes, analysis_intent)

        if tool_context is not None:
            analyzed = list(tool_context.state.get("photos_for_analysis_taken_on") or [])
            analyzed.append(str(photo.taken_on))
            tool_context.state["photos_for_analysis_taken_on"] = analyzed

        return {
            "status": "analysis_complete",
            "bonsai_name": bonsai_name,
            "taken_on": str(photo.taken_on),
            "analysis": analysis,
        }

    return analyze_bonsai_photo


def _select_photo(photos: list, date_hint: str):
    if not date_hint:
        return photos[-1]
    target = _parse_date_hint(date_hint, photos)
    if target is None:
        return photos[-1]
    return min(photos, key=lambda photo: abs((photo.taken_on - target).days))


def _parse_date_hint(date_hint: str, photos: list) -> date | None:
    try:
        return date.fromisoformat(date_hint)
    except ValueError:
        pass

    parts = date_hint.split("-")
    if len(parts) == 2:
        try:
            return date(int(parts[0]), int(parts[1]), 15)
        except ValueError:
            pass

    lower = date_hint.lower()
    for month_name, month_num in _SPANISH_MONTHS.items():
        if month_name in lower:
            years = sorted({photo.taken_on.year for photo in photos})
            return date(years[0], month_num, 15)

    return None
