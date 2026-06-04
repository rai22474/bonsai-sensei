import re
from pathlib import Path


def search_wiki_pages(pattern: str, wiki_root: Path) -> str:
    """Search wiki pages using a regular expression. Returns matching lines as 'path:line_number:content'. Case-insensitive. Pattern is a Python regex (e.g. 'Biorren|biorren', '\\bficus\\b', 'error.*página')."""
    wiki_root_resolved = wiki_root.resolve()
    if not wiki_root_resolved.exists():
        return "No results found."
    try:
        compiled = re.compile(pattern, re.IGNORECASE)
    except re.error as regex_error:
        return f"Invalid regex pattern: {regex_error}"
    results = []
    for page in sorted(wiki_root_resolved.rglob("*.md")):
        relative_path = str(page.relative_to(wiki_root_resolved))
        for line_number, line in enumerate(page.read_text(encoding="utf-8").splitlines(), start=1):
            if compiled.search(line):
                results.append(f"{relative_path}:{line_number}:{line}")
    return "\n".join(results) if results else "No results found."
