import asyncio
import json
import os
from pathlib import Path
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


async def upload_photo_async(photo_bytes: bytes, user_id: str, filename: str = "photo.png") -> dict:
    url = f"{BASE_URL}/api/advice/photos"
    timeout = aiohttp.ClientTimeout(total=180)
    form_data = aiohttp.FormData()
    form_data.add_field("photo", photo_bytes, filename=filename, content_type="image/png")
    form_data.add_field("user_id", user_id)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(url, data=form_data) as response:
            body = await response.text()
            if response.status >= 400:
                raise aiohttp.ClientResponseError(
                    request_info=response.request_info,
                    history=response.history,
                    status=response.status,
                    message=body,
                    headers=response.headers,
                )
            return json.loads(body) if body else {}


def upload_photo(photo_bytes: bytes, user_id: str, filename: str = "photo.png") -> dict:
    return asyncio.run(upload_photo_async(photo_bytes, user_id, filename))


async def post_bonsai_photo_async(bonsai_id: int, photo_bytes: bytes, filename: str = "photo.png") -> dict:
    url = f"{BASE_URL}/api/bonsai/{bonsai_id}/photos"
    timeout = aiohttp.ClientTimeout(total=30)
    form_data = aiohttp.FormData()
    form_data.add_field("file", photo_bytes, filename=filename, content_type="image/png")
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(url, data=form_data) as response:
            body = await response.text()
            if response.status >= 400:
                raise aiohttp.ClientResponseError(
                    request_info=response.request_info,
                    history=response.history,
                    status=response.status,
                    message=body,
                    headers=response.headers,
                )
            return json.loads(body) if body else {}


def post_bonsai_photo(bonsai_id: int, photo_bytes: bytes, filename: str = "photo.png") -> dict:
    return asyncio.run(post_bonsai_photo_async(bonsai_id, photo_bytes, filename))


def accept_confirmation(user_id: str, confirmation_id: str):
    return post(
        f"/api/advice/confirmations/{confirmation_id}/accept",
        {"user_id": user_id},
    )


def reject_confirmation(user_id: str, confirmation_id: str, reason: str = ""):
    return post(
        f"/api/advice/confirmations/{confirmation_id}/reject",
        {"user_id": user_id, "reason": reason},
    )


def choose_selection(user_id: str, selection_id: str, option: str):
    return post(
        f"/api/advice/selections/{selection_id}/choose",
        {"user_id": user_id, "option": option},
    )


def send_text_response(user_id: str, text: str):
    return post("/api/advice/text-response", {"user_id": user_id, "text": text})


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
