import asyncio
import json
import os
import aiohttp

BASE_URL = os.getenv("ACCEPTANCE_API_BASE", "http://localhost:8060")


async def request_json_async(method: str, path: str, payload: dict | None = None):
    url = f"{BASE_URL}{path}"
    timeout = aiohttp.ClientTimeout(total=60)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.request(method, url, json=payload) as response:
            body = await response.text()
            if response.status >= 400:
                raise aiohttp.ClientResponseError(
                    request_info=response.request_info,
                    history=response.history,
                    status=response.status,
                    message=body,
                    headers=response.headers,
                )
            return json.loads(body) if body else None


def request_json(method: str, path: str, payload: dict | None = None):
    return asyncio.run(request_json_async(method, path, payload))
