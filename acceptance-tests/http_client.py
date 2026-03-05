import asyncio
import json
import os
import aiohttp

BASE_URL = os.getenv("ACCEPTANCE_API_BASE", "http://localhost:8060")


async def request_json_async(method: str, path: str, payload: dict | None = None):
    url = f"{BASE_URL}{path}"
    timeout = aiohttp.ClientTimeout(total=180)
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


def get(path: str):
    return request_json("GET", path)


def post(path: str, payload: dict | None = None):
    return request_json("POST", path, payload)


def put(path: str, payload: dict | None = None):
    return request_json("PUT", path, payload)


def delete(path: str):
    return request_json("DELETE", path)


def advise(text: str, user_id: str):
    return post(
        "/api/advice",
        {
            "text": text,
            "user_id": user_id,
        },
    )


def accept_confirmation(user_id: str, confirmation_id: str):
    return post(
        f"/api/advice/confirmations/{confirmation_id}/accept",
        {"user_id": user_id},
    )


def reset_session(user_id: str) -> None:
    delete(f"/api/advice/sessions/{user_id}")


async def post_sse_async(path: str, payload: dict | None = None) -> list[dict]:
    url = f"{BASE_URL}{path}"
    timeout = aiohttp.ClientTimeout(total=300)
    events = []
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(url, json=payload) as response:
            async for raw_line in response.content:
                line = raw_line.decode("utf-8").strip()
                if line.startswith("data: "):
                    event_data = json.loads(line[6:])
                    events.append(event_data)
                    if event_data.get("status") == "done":
                        break
    return events


def post_sse(path: str, payload: dict | None = None) -> list[dict]:
    return asyncio.run(post_sse_async(path, payload))
