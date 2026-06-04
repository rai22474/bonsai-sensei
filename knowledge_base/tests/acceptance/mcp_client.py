import asyncio
import json
import os

from mcp import ClientSession
from mcp.client.sse import sse_client

MCP_URL = os.getenv("ACCEPTANCE_MCP_BASE", "http://localhost:8060/mcp/sse")


async def _call_tool_async(tool_name: str, arguments: dict) -> dict:
    async with sse_client(MCP_URL) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            for content in result.content or []:
                if content.type == "text":
                    try:
                        return json.loads(content.text)
                    except (json.JSONDecodeError, ValueError):
                        return {"content": content.text}
            return {}


def call_tool(tool_name: str, arguments: dict) -> dict:
    return asyncio.run(_call_tool_async(tool_name, arguments))


def write_wiki_page(path: str, content: str) -> dict:
    """Write a wiki page via MCP."""
    return call_tool("write_wiki_page", {"path": path, "content": content})


def read_wiki_page(path: str) -> dict | None:
    """Read a wiki page via MCP. Returns None if not found."""
    result = call_tool("read_wiki_page", {"path": path})
    if result.get("status") == "error":
        return None
    return result


def list_wiki_files(directory: str = "", pattern: str = "*.md") -> list[str]:
    """List wiki files via MCP."""
    result = call_tool("list_wiki_files", {"directory": directory, "pattern": pattern})
    if isinstance(result, list):
        return result
    return result.get("files", [])


def search_wiki(query: str, top_k: int = 5) -> list[dict]:
    """Search wiki via MCP semantic search."""
    result = call_tool("search_wiki_knowledge", {"query": query, "top_k": top_k})
    return result.get("results", [])
