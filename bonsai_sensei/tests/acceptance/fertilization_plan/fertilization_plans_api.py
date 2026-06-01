from datetime import date, timezone
from typing import Callable


def create_fertilization_plan(post: Callable, bonsai_id: int, period_start: str, period_end: str) -> dict:
    payload = {
        "bonsai_id": bonsai_id,
        "period_start": period_start,
        "period_end": period_end,
        "status": "active",
        "wiki_path": f"bonsai/test/plans/{period_start[:7]}_to_{period_end[:7]}.md",
        "created_at": date.today().isoformat(),
    }
    return post(f"/api/bonsai/{bonsai_id}/fertilization-plans", payload)


def get_active_fertilization_plan(get: Callable, bonsai_id: int) -> dict | None:
    try:
        return get(f"/api/bonsai/{bonsai_id}/fertilization-plans/active")
    except Exception:
        return None


def list_fertilization_plans(get: Callable, bonsai_id: int) -> list:
    return get(f"/api/bonsai/{bonsai_id}/fertilization-plans")


def delete_fertilization_plan(delete: Callable, plan_id: int) -> None:
    try:
        delete(f"/api/fertilization-plans/{plan_id}")
    except Exception:
        pass
