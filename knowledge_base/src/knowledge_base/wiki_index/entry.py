import re
from dataclasses import dataclass


@dataclass
class IndexEntry:
    page_path: str
    abstract: str
    links: list[str]
    embedding: list[float]
    user_id: str | None = None


def extract_abstract(content: str) -> str:
    """Extract title + first 3 non-empty non-heading non-bullet lines, max 500 chars."""
    lines = content.splitlines()
    title_lines = [line for line in lines if line.startswith("#")]
    body_lines = [
        line for line in lines
        if line.strip()
        and not line.startswith("#")
        and not line.startswith("-")
        and not line.startswith("*")
        and not line.startswith(">")
    ]
    selected_lines = title_lines[:1] + body_lines[:3]
    return "\n".join(selected_lines)[:500]


def extract_links(content: str) -> list[str]:
    """Extract all [[path|text]] and [[path]] wikilink paths from markdown content."""
    return re.findall(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", content)
