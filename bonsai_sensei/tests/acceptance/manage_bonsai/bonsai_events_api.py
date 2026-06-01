from typing import Callable


def list_bonsai_events(get_func: Callable[[str], list | None], bonsai_id: int) -> list[dict]:
    return get_func(f"/api/bonsai/{bonsai_id}/events") or []


def record_bonsai_event(post_func: Callable, bonsai_id: int, event_type: str, payload: dict) -> dict:
    return post_func(
        f"/api/bonsai/{bonsai_id}/events",
        {"event_type": event_type, "payload": payload},
    )
