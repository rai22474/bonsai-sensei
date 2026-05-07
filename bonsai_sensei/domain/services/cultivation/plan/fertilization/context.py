import re
from typing import Callable

from bonsai_sensei.domain.services.cultivation.plan.fertilization.wiki import read_wiki_content


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


def _format_event(event: dict) -> str:
    occurred_at = event.get("occurred_at", "")
    date_str = occurred_at[:10] if occurred_at else "unknown date"
    payload_parts = ", ".join(f"{key}: {value}" for key, value in (event.get("payload") or {}).items())
    return f"{date_str} | {event.get('event_type', '')}" + (f" | {payload_parts}" if payload_parts else "")
