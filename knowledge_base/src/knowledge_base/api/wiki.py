import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class WriteWikiPageRequest(BaseModel):
    path: str
    content: str


@router.put("/wiki", status_code=200)
def write_wiki_page(body: WriteWikiPageRequest):
    """Write content to a wiki page at the given path. Creates parent directories if needed."""
    wiki_root = Path(os.getenv("WIKI_PATH", "./wiki")).resolve()
    resolved = (wiki_root / body.path).resolve()

    if not str(resolved).startswith(str(wiki_root)):
        raise HTTPException(status_code=400, detail="invalid_path")

    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(body.content, encoding="utf-8")
    return {"status": "written", "path": body.path}


@router.get("/wiki")
def get_wiki_page(path: str):
    wiki_root = Path(os.getenv("WIKI_PATH", "./wiki")).resolve()
    resolved = (wiki_root / path).resolve()

    if not str(resolved).startswith(str(wiki_root)):
        raise HTTPException(status_code=400, detail="invalid_path")

    if not resolved.exists():
        raise HTTPException(status_code=404, detail="page_not_found")

    return {"content": resolved.read_text(encoding="utf-8")}


@router.delete("/wiki")
def delete_wiki_page(path: str):
    wiki_root = Path(os.getenv("WIKI_PATH", "./wiki")).resolve()
    resolved = (wiki_root / path).resolve()

    if not str(resolved).startswith(str(wiki_root)):
        raise HTTPException(status_code=400, detail="invalid_path")

    if not resolved.exists():
        raise HTTPException(status_code=404, detail="page_not_found")

    resolved.unlink()
    return {"status": "deleted", "path": path}


@router.get("/wiki/files")
def list_wiki_files(directory: str = "", pattern: str = "*.md"):
    """List wiki files in a directory matching a glob pattern."""
    wiki_root = Path(os.getenv("WIKI_PATH", "./wiki")).resolve()
    target = (wiki_root / directory).resolve()
    if not str(target).startswith(str(wiki_root)):
        raise HTTPException(status_code=400, detail="invalid_path")
    if not target.is_dir():
        return []
    return [str(path.relative_to(wiki_root)) for path in sorted(target.glob(pattern))]
