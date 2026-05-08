from datetime import date
from typing import Callable


def read_wiki_content(wiki_path: str, read_wiki_page_func: Callable) -> str:
    page = read_wiki_page_func(path=wiki_path)
    return page.get("content", "") if page.get("status") == "success" else ""


def update_wiki_on_abandon(
    wiki_path: str,
    reason: str,
    read_wiki_page_func: Callable,
    write_wiki_page_func: Callable,
) -> None:
    updated = read_wiki_content(wiki_path, read_wiki_page_func).replace("**Status:** active", "**Status:** abandoned")
    if "## Abandonment" not in updated:
        updated += f"\n## Abandonment\n\n**Date:** {date.today().isoformat()}\n**Reason:** {reason}\n"
    write_wiki_page_func(path=wiki_path, content=updated)
