from typing import List, Dict, Optional
from urllib.parse import urlparse
from ddgs import DDGS
import trafilatura

def crawl_web(
    query: str,
    max_sources: int = 3,
    allowed_domains: Optional[List[str]] = None,
) -> List[Dict[str, str]]:
    if not query:
        return []
    if not allowed_domains:
        return []
    sources = []
    seen_urls = set()
    with DDGS() as client:
        for search_query in _build_queries(query, allowed_domains):
            for result in _search_results(client, search_query, max_sources=max_sources):
                url = result.get("href") or result.get("url") or ""
                title = result.get("title") or ""
                if not url:
                    continue
                if allowed_domains and not _is_allowed_domain(url, allowed_domains):
                    continue
                if url in seen_urls:
                    continue
                content = _extract_text(url)
                if not content:
                    continue
                sources.append({"title": title, "url": url, "content": content[:1200]})
                seen_urls.add(url)
                if len(sources) >= max_sources:
                    return sources
    return sources


def _build_queries(query: str, allowed_domains: Optional[List[str]]) -> List[str]:
    if not allowed_domains:
        return [query]
    return [f"site:{domain} {query}" for domain in allowed_domains]


def _search_results(client: object, query: str, max_sources: int) -> List[Dict[str, str]]:
    try:
        return list(client.text(query, max_results=max_sources))
    except Exception:
        return []


def _extract_text(url: str) -> str:
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        return ""
    extracted = trafilatura.extract(downloaded)
    if not extracted:
        return ""
    return extracted


def _is_allowed_domain(url: str, allowed_domains: List[str]) -> bool:
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    normalized = hostname.lower()
    for domain in allowed_domains:
        candidate = domain.lower().lstrip(".")
        if normalized == candidate or normalized.endswith(f".{candidate}"):
            return True
    return False


crawl_web.__doc__ = "Crawl the web for a query and return top sources with extracted text."
