import re
from pathlib import Path


def replace_in_pages(pattern: str, replacement: str, wiki_root: Path, max_pages: int = 5) -> str:
    """Replace all regex matches in wiki pages, processing up to max_pages pages per call.

    Use this for bulk corrections across many pages (e.g. fixing a misspelling everywhere).
    Returns a summary of pages fixed and how many still have pending matches — repeat the
    call to continue processing the remaining pages.

    Args:
        pattern: Python regex to search for (case-insensitive).
        replacement: Literal string to replace each match with.
        max_pages: Maximum pages to process in this call (default 5).
    """
    wiki_root_resolved = wiki_root.resolve()
    try:
        compiled = re.compile(pattern, re.IGNORECASE)
    except re.error as regex_error:
        return f"Invalid regex pattern: {regex_error}"

    pages_with_matches = [
        page for page in sorted(wiki_root_resolved.rglob("*.md"))
        if compiled.search(page.read_text(encoding="utf-8"))
    ]

    total_remaining = len(pages_with_matches)
    if total_remaining == 0:
        return f"No pages contain matches for '{pattern}'."

    batch = pages_with_matches[:max_pages]
    fixed = []
    for page in batch:
        content = page.read_text(encoding="utf-8")
        page.write_text(compiled.sub(replacement, content), encoding="utf-8")
        fixed.append(str(page.relative_to(wiki_root_resolved)))

    still_pending = total_remaining - len(batch)
    summary = f"Fixed {len(fixed)} page(s): {', '.join(fixed)}."
    if still_pending > 0:
        summary += f" {still_pending} page(s) still have matches — repeat the command to continue."
    else:
        summary += " No more pages with matches."
    return summary
