from typing import Callable

import aiohttp


def list_planned_works(get_func: Callable[[str], list | None], bonsai_id: int) -> list[dict]:
    return get_func(f"/api/bonsai/{bonsai_id}/planned-works") or []


def create_planned_work(
    post_func: Callable[[str, dict | None], dict | None],
    bonsai_id: int,
    work_type: str,
    payload: dict,
    scheduled_date: str,
    notes: str | None = None,
) -> dict:
    body = {
        "bonsai_id": bonsai_id,
        "work_type": work_type,
        "payload": payload,
        "scheduled_date": scheduled_date,
    }
    if notes:
        body["notes"] = notes
    return post_func(f"/api/bonsai/{bonsai_id}/planned-works", body) or {}


def delete_planned_work(delete_func: Callable[[str], dict | None], work_id: int) -> None:
    try:
        delete_func(f"/api/bonsai/planned-works/{work_id}")
    except aiohttp.ClientResponseError as exc:
        if exc.status == 404:
            return
        raise
