import re
from datetime import date
from typing import Callable

from google.adk.tools.tool_context import ToolContext

_SPANISH_MONTHS = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}


def create_show_bonsai_photo_tool(
    get_bonsai_by_name_func: Callable,
    list_bonsai_photos_func: Callable,
) -> Callable:
    async def show_bonsai_photo(
        bonsai_name: str,
        date_hint: str = "",
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Display a single stored photo of a bonsai. Use this when the user asks to see,
        show, or retrieve a particular photo — by exact date, approximate date ("marzo"),
        closest to a given date, or the latest one. Sends only the selected photo to the user.

        Do not use this when the user asks to see all photos at once; use show_bonsai_photos for that.

        Args:
            bonsai_name: Name of the bonsai.
            date_hint: Date reference in natural language or ISO format
                       (e.g. "1 de abril de 2026", "marzo 2026", "2026-03-10", "más cercana al 15 de mayo").
                       Leave empty to select the latest photo.

        Returns:
            JSON with status 'success' or 'error'.
            Output JSON (success): {"status": "success", "photo": {"id": int, "file_path": str, "taken_on": "YYYY-MM-DD"}}.
            Output JSON (error): {"status": "error", "message": "bonsai_not_found" | "no_photos"}.
        """
        bonsai = get_bonsai_by_name_func(bonsai_name)
        if not bonsai:
            return {"status": "error", "message": "bonsai_not_found"}
        photos = list_bonsai_photos_func(bonsai_id=bonsai.id)
        if not photos:
            return {"status": "error", "message": "no_photos"}
        photo = _select_closest_photo(photos, date_hint)
        if tool_context is not None:
            tool_context.state["photos_to_display"] = [photo.file_path]
        return {
            "status": "success",
            "photo": {"id": photo.id, "file_path": photo.file_path, "taken_on": str(photo.taken_on)},
        }

    return show_bonsai_photo


def _select_closest_photo(photos: list, date_hint: str):
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
            day_match = re.search(r'\b(\d{1,2})\b', date_hint)
            year_match = re.search(r'\b(20\d{2})\b', date_hint)
            day = int(day_match.group(1)) if day_match else 15
            if year_match:
                return date(int(year_match.group(1)), month_num, day)
            years = sorted({photo.taken_on.year for photo in photos})
            return date(years[0], month_num, day)

    return None
