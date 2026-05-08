from typing import Callable


def create_phytosanitary_plan(post: Callable, bonsai_id: int, period_start: str, period_end: str) -> dict:
    payload = {
        "bonsai_id": bonsai_id,
        "period_start": period_start,
        "period_end": period_end,
        "status": "active",
        "wiki_path": f"bonsai/test/phytosanitary-plans/{period_start[:7]}_to_{period_end[:7]}.md",
    }
    return post(f"/api/bonsai/{bonsai_id}/phytosanitary-plans", payload)


def get_active_phytosanitary_plan(get: Callable, bonsai_id: int) -> dict | None:
    try:
        return get(f"/api/bonsai/{bonsai_id}/phytosanitary-plans/active")
    except Exception:
        return None


def list_phytosanitary_plans(get: Callable, bonsai_id: int) -> list:
    return get(f"/api/bonsai/{bonsai_id}/phytosanitary-plans")


def delete_phytosanitary_plan(delete: Callable, plan_id: int) -> None:
    try:
        delete(f"/api/phytosanitary-plans/{plan_id}")
    except Exception:
        pass
