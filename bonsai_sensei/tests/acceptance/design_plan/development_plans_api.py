from datetime import date
from typing import Callable


def create_development_plan(post: Callable, bonsai_id: int, period_start: str, period_end: str) -> dict:
    payload = {
        "bonsai_id": bonsai_id,
        "development_path": "planton",
        "current_phase": "engorde",
        "target_style": "moyogi",
        "design_goal": "Test plan",
        "period_start": period_start,
        "period_end": period_end,
        "status": "active",
        "wiki_path": f"bonsai/test/design-plans/{period_start[:7]}_to_{period_end[:7]}.md",
        "created_at": date.today().isoformat(),
    }
    return post(f"/api/bonsai/{bonsai_id}/development-plans", payload)


def get_active_development_plan(get: Callable, bonsai_id: int) -> dict | None:
    try:
        return get(f"/api/bonsai/{bonsai_id}/development-plans/active")
    except Exception:
        return None


def list_development_plans(get: Callable, bonsai_id: int) -> list:
    return get(f"/api/bonsai/{bonsai_id}/development-plans")


def delete_development_plan(delete: Callable, plan_id: int) -> None:
    try:
        delete(f"/api/development-plans/{plan_id}")
    except Exception:
        pass
