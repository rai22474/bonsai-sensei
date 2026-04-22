import os
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/wiki")
def get_wiki_page(path: str):
    wiki_root = Path(os.getenv("WIKI_PATH", "./wiki")).resolve()
    resolved = (wiki_root / path).resolve()

    if not str(resolved).startswith(str(wiki_root)):
        raise HTTPException(status_code=400, detail="invalid_path")

    if not resolved.exists():
        raise HTTPException(status_code=404, detail="page_not_found")

    return {"content": resolved.read_text(encoding="utf-8")}
