from typing import Callable, List

from fastapi import APIRouter, Depends, HTTPException, Request

from bonsai_sensei.domain.fertilization_plan import FertilizationPlan

router = APIRouter()


def get_list_fertilization_plans_svc(request: Request) -> Callable:
    return request.app.state.fertilization_plan_service["list_fertilization_plans"]


def get_get_fertilization_plan_svc(request: Request) -> Callable:
    return request.app.state.fertilization_plan_service["get_fertilization_plan"]


def get_delete_fertilization_plan_svc(request: Request) -> Callable:
    return request.app.state.fertilization_plan_service["delete_fertilization_plan"]


def get_create_fertilization_plan_svc(request: Request) -> Callable:
    return request.app.state.fertilization_plan_service["create_fertilization_plan"]


def get_active_plan_svc(request: Request) -> Callable:
    return request.app.state.fertilization_plan_service["get_active_fertilization_plan"]


@router.get("/bonsai/{bonsai_id}/fertilization-plans", response_model=List[FertilizationPlan])
def list_bonsai_fertilization_plans(
    bonsai_id: int,
    list_fertilization_plans_func: Callable = Depends(get_list_fertilization_plans_svc),
):
    return list_fertilization_plans_func(bonsai_id=bonsai_id)


@router.post("/bonsai/{bonsai_id}/fertilization-plans", response_model=FertilizationPlan)
def create_bonsai_fertilization_plan(
    bonsai_id: int,
    plan: FertilizationPlan,
    create_fertilization_plan_func: Callable = Depends(get_create_fertilization_plan_svc),
):
    plan.id = None
    plan.bonsai_id = bonsai_id
    return create_fertilization_plan_func(plan=plan)


@router.get("/bonsai/{bonsai_id}/fertilization-plans/active", response_model=FertilizationPlan)
def get_active_bonsai_fertilization_plan(
    bonsai_id: int,
    get_active_plan_func: Callable = Depends(get_active_plan_svc),
):
    plan = get_active_plan_func(bonsai_id=bonsai_id)
    if not plan:
        raise HTTPException(status_code=404, detail="No active fertilization plan found")
    return plan


@router.get("/fertilization-plans/{plan_id}", response_model=FertilizationPlan)
def get_fertilization_plan(
    plan_id: int,
    get_fertilization_plan_func: Callable = Depends(get_get_fertilization_plan_svc),
):
    plan = get_fertilization_plan_func(plan_id=plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Fertilization plan not found")
    return plan


@router.delete("/fertilization-plans/{plan_id}")
def delete_fertilization_plan(
    plan_id: int,
    delete_fertilization_plan_func: Callable = Depends(get_delete_fertilization_plan_svc),
):
    success = delete_fertilization_plan_func(plan_id=plan_id)
    if not success:
        raise HTTPException(status_code=404, detail="Fertilization plan not found")
    return {"status": "success", "message": f"Fertilization plan {plan_id} deleted"}
