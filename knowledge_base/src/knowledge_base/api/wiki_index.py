import os
from functools import partial
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from knowledge_base.wiki_index.indexer import build_full_index

router = APIRouter(prefix="/wiki/index", tags=["wiki-index"])


@router.post("/rebuild", status_code=200)
async def rebuild_wiki_index(request: Request):
    """Rebuild the full wiki semantic index. Embeds all .md pages. May take 30-60s."""
    embed = getattr(request.app.state, "embed_text", None)
    if embed is None:
        raise HTTPException(status_code=503, detail="embedder_not_configured")
    wiki_root = Path(os.getenv("WIKI_PATH", "./wiki"))
    count = await build_full_index(wiki_root, embed)
    return {"indexed_pages": count}


class WikiSearchRequest(BaseModel):
    query: str
    top_k: int = 5


@router.post("/search", status_code=200)
async def search_wiki_index(body: WikiSearchRequest, request: Request):
    """Search the wiki knowledge base semantically. Returns top matching pages with path, abstract, and score."""
    embed = getattr(request.app.state, "embed_text", None)
    if embed is None:
        raise HTTPException(status_code=503, detail="embedder_not_configured")
    from knowledge_base.wiki_index.searcher import search_by_embedding
    from knowledge_base.wiki_index.store import load_all_entries
    wiki_root = Path(os.getenv("WIKI_PATH", "./wiki"))
    entry_loader = partial(load_all_entries, wiki_root)
    search_index = partial(search_by_embedding, load_entries=entry_loader)
    query_embedding = await embed(body.query)
    results = search_index(query_embedding)[:body.top_k]
    return {
        "results": [
            {"page_path": page_path, "abstract": abstract, "score": round(score, 3)}
            for page_path, abstract, score in results
        ]
    }
