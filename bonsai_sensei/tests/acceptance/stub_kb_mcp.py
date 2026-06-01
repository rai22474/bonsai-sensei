import json
import os

from fastapi import FastAPI, HTTPException
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import TextContent, Tool
from pydantic import BaseModel
from starlette.applications import Starlette
from starlette.routing import Mount, Route

_wiki: dict[str, str] = {}

_mcp_server = Server("kb-stub")


@_mcp_server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="read_wiki_page",
            description="Read a wiki page.",
            inputSchema={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
        ),
        Tool(
            name="write_wiki_page",
            description="Write a wiki page.",
            inputSchema={
                "type": "object",
                "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
                "required": ["path", "content"],
            },
        ),
        Tool(
            name="list_wiki_files",
            description="List wiki files.",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "default": ""},
                    "pattern": {"type": "string", "default": "*.md"},
                },
            },
        ),
        Tool(
            name="search_wiki_knowledge",
            description="Search wiki.",
            inputSchema={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
        ),
    ]


@_mcp_server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "read_wiki_page":
        path = arguments["path"]
        if path in _wiki:
            result = {"status": "success", "content": _wiki[path]}
        else:
            result = {"status": "error", "message": "page_not_found"}

    elif name == "write_wiki_page":
        _wiki[arguments["path"]] = arguments["content"]
        result = {"status": "success", "path": arguments["path"]}

    elif name == "list_wiki_files":
        directory = arguments.get("directory", "")
        pattern = arguments.get("pattern", "*.md")
        suffix = pattern.lstrip("*")
        files = sorted(path for path in _wiki if path.startswith(directory) and path.endswith(suffix))
        result = files

    elif name == "search_wiki_knowledge":
        result = {"results": []}

    else:
        result = {"error": f"unknown_tool: {name}"}

    return [TextContent(type="text", text=json.dumps(result))]


_sse_transport = SseServerTransport("/messages/")


async def _handle_sse(request):
    async with _sse_transport.connect_sse(request.scope, request.receive, request._send) as streams:
        await _mcp_server.run(streams[0], streams[1], _mcp_server.create_initialization_options())


_mcp_starlette = Starlette(
    routes=[
        Route("/sse", endpoint=_handle_sse),
        Mount("/messages/", app=_sse_transport.handle_post_message),
    ]
)

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


@app.post("/api/wiki/reset", status_code=200)
def reset_wiki():
    _wiki.clear()
    return {"status": "reset"}


app.mount("/mcp", _mcp_starlette)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
