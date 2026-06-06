from typing import Callable, List

from fastapi import APIRouter, Depends, HTTPException, Request

from bonsai_sensei.domain.development_plan import DevelopmentPlan

router = APIRouter()


def get_list_development_plans_svc(request: Request) -> Callable:
    return request.app.state.development_plan_service["list_development_plans"]


def get_get_development_plan_svc(request: Request) -> Callable:
    return request.app.state.development_plan_service["get_development_plan"]


def get_delete_development_plan_svc(request: Request) -> Callable:
    return request.app.state.development_plan_service["delete_development_plan"]


def get_create_development_plan_svc(request: Request) -> Callable:
    return request.app.state.development_plan_service["create_development_plan"]


def get_active_plan_svc(request: Request) -> Callable:
    return request.app.state.development_plan_service["get_active_development_plan"]


@router.get("/bonsai/{bonsai_id}/development-plans", response_model=List[DevelopmentPlan])
def list_bonsai_development_plans(
    bonsai_id: int,
    list_development_plans_func: Callable = Depends(get_list_development_plans_svc),
):
    return list_development_plans_func(bonsai_id=bonsai_id)


@router.post("/bonsai/{bonsai_id}/development-plans", response_model=DevelopmentPlan)
def create_bonsai_development_plan(
    bonsai_id: int,
    plan: DevelopmentPlan,
    create_development_plan_func: Callable = Depends(get_create_development_plan_svc),
):
    plan.id = None
    plan.bonsai_id = bonsai_id
    return create_development_plan_func(plan=plan)


@router.get("/bonsai/{bonsai_id}/development-plans/active", response_model=DevelopmentPlan)
def get_active_bonsai_development_plan(
    bonsai_id: int,
    get_active_plan_func: Callable = Depends(get_active_plan_svc),
):
    plan = get_active_plan_func(bonsai_id=bonsai_id)
    if not plan:
        raise HTTPException(status_code=404, detail="No active development plan found")
    return plan


@router.get("/development-plans/{plan_id}", response_model=DevelopmentPlan)
def get_development_plan(
    plan_id: int,
    get_development_plan_func: Callable = Depends(get_get_development_plan_svc),
):
    plan = get_development_plan_func(plan_id=plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Development plan not found")
    return plan


@router.delete("/development-plans/{plan_id}")
def delete_development_plan(
    plan_id: int,
    delete_development_plan_func: Callable = Depends(get_delete_development_plan_svc),
):
    success = delete_development_plan_func(plan_id=plan_id)
    if not success:
        raise HTTPException(status_code=404, detail="Development plan not found")
    return {"status": "success", "message": f"Development plan {plan_id} deleted"}
