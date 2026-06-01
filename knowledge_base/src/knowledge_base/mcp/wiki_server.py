import json
from pathlib import Path
from typing import Callable

from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import TextContent, Tool
from starlette.applications import Starlette
from starlette.routing import Mount, Route


def create_wiki_mcp_server(wiki_root: Path, embed_func: Callable | None = None, search_index: Callable | None = None) -> tuple[Server, SseServerTransport]:
    """Create an MCP server exposing wiki tools. Returns (server, transport)."""
    server = Server("knowledge-base-wiki")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="read_wiki_page",
                description="Read the content of a wiki page by its path relative to the wiki root. Use for care guides, disease profiles, fertilizer sheets.",
                inputSchema={
                    "type": "object",
                    "properties": {"path": {"type": "string", "description": "Path relative to wiki root (e.g. 'species/ficus-retusa.md')"}},
                    "required": ["path"],
                },
            ),
            Tool(
                name="write_wiki_page",
                description="Write content to a wiki page at the given path relative to the wiki root. Creates parent directories if needed.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path relative to wiki root"},
                        "content": {"type": "string", "description": "Full markdown content"},
                    },
                    "required": ["path", "content"],
                },
            ),
            Tool(
                name="list_wiki_files",
                description="List wiki files in a directory matching a glob pattern.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "directory": {"type": "string", "description": "Directory relative to wiki root", "default": ""},
                        "pattern": {"type": "string", "description": "Glob pattern", "default": "*.md"},
                    },
                },
            ),
            Tool(
                name="search_wiki_knowledge",
                description="Semantically search the wiki knowledge base. Use before answering questions about species, fertilizers, techniques, pests.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "top_k": {"type": "integer", "description": "Number of results", "default": 5},
                    },
                    "required": ["query"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        if name == "read_wiki_page":
            path = arguments["path"]
            wiki_root_path = wiki_root.resolve()
            resolved = (wiki_root_path / path).resolve()
            if not str(resolved).startswith(str(wiki_root_path)):
                result = {"status": "error", "message": "invalid_path"}
            elif not resolved.exists():
                result = {"status": "error", "message": "page_not_found"}
            else:
                result = {"status": "success", "content": resolved.read_text(encoding="utf-8")}

        elif name == "write_wiki_page":
            path = arguments["path"]
            content = arguments["content"]
            wiki_root_path = wiki_root.resolve()
            resolved = (wiki_root_path / path).resolve()
            if not str(resolved).startswith(str(wiki_root_path)):
                result = {"status": "error", "message": "invalid_path"}
            else:
                resolved.parent.mkdir(parents=True, exist_ok=True)
                resolved.write_text(content, encoding="utf-8")
                result = {"status": "success", "path": path}

        elif name == "list_wiki_files":
            directory = arguments.get("directory", "")
            pattern = arguments.get("pattern", "*.md")
            wiki_root_path = wiki_root.resolve()
            target = (wiki_root_path / directory).resolve()
            if not str(target).startswith(str(wiki_root_path)) or not target.is_dir():
                result = []
            else:
                result = [str(path.relative_to(wiki_root_path)) for path in sorted(target.glob(pattern))]

        elif name == "search_wiki_knowledge":
            if embed_func is None or search_index is None:
                result = {"results": []}
            else:
                query = arguments["query"]
                top_k = arguments.get("top_k", 5)
                query_embedding = await embed_func(query)
                results = search_index(query_embedding)[:top_k]
                result = {
                    "results": [
                        {"page_path": page_path, "abstract": abstract, "score": round(score, 3)}
                        for page_path, abstract, score in results
                    ]
                }
        else:
            result = {"error": f"unknown_tool: {name}"}

        return [TextContent(type="text", text=json.dumps(result))]

    sse_transport = SseServerTransport("/messages/")
    return server, sse_transport


def build_mcp_starlette_app(server: Server, sse_transport: SseServerTransport) -> Starlette:
    """Build a Starlette app exposing the MCP server at /sse."""

    async def handle_sse(request):
        async with sse_transport.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await server.run(
                streams[0], streams[1], server.create_initialization_options()
            )

    return Starlette(
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse_transport.handle_post_message),
        ]
    )
