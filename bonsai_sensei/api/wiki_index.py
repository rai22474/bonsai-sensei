import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request

from bonsai_sensei.knowledge_base.wiki_index.indexer import build_full_index

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
