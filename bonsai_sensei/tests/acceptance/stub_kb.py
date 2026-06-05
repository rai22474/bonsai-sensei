import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

_wiki: dict[str, str] = {}

app = FastAPI(title="KB Stub")


class WriteWikiRequest(BaseModel):
    path: str
    content: str


@app.put("/api/wiki", status_code=200)
def write_wiki_page(body: WriteWikiRequest):
    _wiki[body.path] = body.content
    return {"status": "written", "path": body.path}


@app.get("/api/wiki")
def get_wiki_page(path: str):
    if path not in _wiki:
        raise HTTPException(status_code=404, detail="page_not_found")
    return {"content": _wiki[path]}


@app.delete("/api/wiki")
def delete_wiki_page(path: str):
    _wiki.pop(path, None)
    return {"status": "deleted", "path": path}


@app.get("/api/wiki/files")
def list_wiki_files(directory: str = "", pattern: str = "*.md"):
    suffix = pattern.lstrip("*")
    return sorted(path for path in _wiki if path.startswith(directory) and path.endswith(suffix))


@app.post("/api/wiki/index/search", status_code=200)
def search_wiki_index(body: dict):
    return {"results": []}


@app.post("/api/wiki/reset", status_code=200)
def reset_wiki():
    _wiki.clear()
    return {"status": "reset"}


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
