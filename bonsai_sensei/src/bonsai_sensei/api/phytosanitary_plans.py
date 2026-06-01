from typing import Callable, List

from fastapi import APIRouter, Depends, HTTPException, Request

from bonsai_sensei.domain.phytosanitary_plan import PhytosanitaryPlan

router = APIRouter()


def get_list_phytosanitary_plans_svc(request: Request) -> Callable:
    return request.app.state.phytosanitary_plan_service["list_phytosanitary_plans"]


def get_get_phytosanitary_plan_svc(request: Request) -> Callable:
    return request.app.state.phytosanitary_plan_service["get_phytosanitary_plan"]


def get_delete_phytosanitary_plan_svc(request: Request) -> Callable:
    return request.app.state.phytosanitary_plan_service["delete_phytosanitary_plan"]


def get_create_phytosanitary_plan_svc(request: Request) -> Callable:
    return request.app.state.phytosanitary_plan_service["create_phytosanitary_plan"]


def get_active_plan_svc(request: Request) -> Callable:
    return request.app.state.phytosanitary_plan_service["get_active_phytosanitary_plan"]


@router.get("/bonsai/{bonsai_id}/phytosanitary-plans", response_model=List[PhytosanitaryPlan])
def list_bonsai_phytosanitary_plans(
    bonsai_id: int,
    list_phytosanitary_plans_func: Callable = Depends(get_list_phytosanitary_plans_svc),
):
    return list_phytosanitary_plans_func(bonsai_id=bonsai_id)


@router.post("/bonsai/{bonsai_id}/phytosanitary-plans", response_model=PhytosanitaryPlan)
def create_bonsai_phytosanitary_plan(
    bonsai_id: int,
    plan: PhytosanitaryPlan,
    create_phytosanitary_plan_func: Callable = Depends(get_create_phytosanitary_plan_svc),
):
    plan.id = None
    plan.bonsai_id = bonsai_id
    return create_phytosanitary_plan_func(plan=plan)


@router.get("/bonsai/{bonsai_id}/phytosanitary-plans/active", response_model=PhytosanitaryPlan)
def get_active_bonsai_phytosanitary_plan(
    bonsai_id: int,
    get_active_plan_func: Callable = Depends(get_active_plan_svc),
):
    plan = get_active_plan_func(bonsai_id=bonsai_id)
    if not plan:
        raise HTTPException(status_code=404, detail="No active phytosanitary plan found")
    return plan


@router.get("/phytosanitary-plans/{plan_id}", response_model=PhytosanitaryPlan)
def get_phytosanitary_plan(
    plan_id: int,
    get_phytosanitary_plan_func: Callable = Depends(get_get_phytosanitary_plan_svc),
):
    plan = get_phytosanitary_plan_func(plan_id=plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Phytosanitary plan not found")
    return plan


@router.delete("/phytosanitary-plans/{plan_id}")
def delete_phytosanitary_plan(
    plan_id: int,
    delete_phytosanitary_plan_func: Callable = Depends(get_delete_phytosanitary_plan_svc),
):
    success = delete_phytosanitary_plan_func(plan_id=plan_id)
    if not success:
        raise HTTPException(status_code=404, detail="Phytosanitary plan not found")
    return {"status": "success", "message": f"Phytosanitary plan {plan_id} deleted"}
