import re
from typing import Callable

from bonsai_sensei.domain.services.cultivation.plan.wiki_utils import read_wiki_content


def load_bonsai_plan_context(
    bonsai,
    bonsai_name: str,
    list_bonsai_events_func: Callable,
    list_wiki_files_func: Callable,
    read_wiki_page_func: Callable,
) -> dict:
    """Load shared context variables used by plan creation and evaluation prompts."""
    slug = bonsai_slug(bonsai_name)
    events = list_bonsai_events_func(bonsai.id) or []
    return {
        "events": [_format_event(event) for event in events],
        "reports": _load_reports(slug, list_wiki_files_func, read_wiki_page_func),
        "bonsai_wiki_content": read_wiki_content(bonsai.wiki_path, read_wiki_page_func) if bonsai.wiki_path else "",
    }


def bonsai_slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _load_reports(slug: str, list_wiki_files_func: Callable, read_wiki_page_func: Callable) -> list[str]:
    paths = list_wiki_files_func(f"bonsai/{slug}/reports")
    reports = []
    for path in paths[-5:]:
        page = read_wiki_page_func(path=path)
        if page.get("status") == "success":
            reports.append(page["content"])
    return reports


_PAYLOAD_SKIP_KEYS = {"development_plan_id", "fertilizer_id", "phytosanitary_id", "wiki_path"}


def _format_event(event: dict) -> str:
    occurred_at = event.get("occurred_at", "")
    date_str = occurred_at[:10] if occurred_at else "unknown date"
    payload = event.get("payload") or {}

    phase = payload.get("development_phase") or payload.get("phase_abandoned")
    phase_prefix = f"[fase: {phase}] " if phase else ""

    result = payload.get("result")
    result_suffix = f" → resultado: {result}" if result else ""

    visible_keys = {key: value for key, value in payload.items() if key not in _PAYLOAD_SKIP_KEYS}
    skip_in_summary = {"development_phase", "phase_abandoned", "result"}
    summary_parts = [
        f"{key}: {value}"
        for key, value in visible_keys.items()
        if key not in skip_in_summary
    ]
    payload_str = ", ".join(summary_parts)

    line = f"{date_str} | {phase_prefix}{event.get('event_type', '')}"
    if payload_str:
        line += f" | {payload_str}"
    line += result_suffix
    return line
