from typing import Callable


def list_bonsai_events(get_func: Callable[[str], list | None], bonsai_id: int) -> list[dict]:
    return get_func(f"/api/bonsai/{bonsai_id}/events") or []
