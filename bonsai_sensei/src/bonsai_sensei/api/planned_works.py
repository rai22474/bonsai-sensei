from typing import Any, Callable, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request

from bonsai_sensei.domain.planned_work import PlannedWork

router = APIRouter()


def get_list_planned_works_svc(request: Request) -> Callable:
    return request.app.state.cultivation_plan_service["list_planned_works"]


def get_create_planned_work_svc(request: Request) -> Callable:
    return request.app.state.cultivation_plan_service["create_planned_work"]


def get_delete_planned_work_svc(request: Request) -> Callable:
    return request.app.state.cultivation_plan_service["delete_planned_work"]


@router.get("/bonsai/{bonsai_id}/planned-works", response_model=List[PlannedWork])
def list_bonsai_planned_works(
    bonsai_id: int,
    list_planned_works_func: Callable = Depends(get_list_planned_works_svc),
):
    return list_planned_works_func(bonsai_id=bonsai_id)


@router.post("/bonsai/{bonsai_id}/planned-works", response_model=PlannedWork)
def create_bonsai_planned_work(
    bonsai_id: int,
    planned_work: PlannedWork,
    create_planned_work_func: Callable = Depends(get_create_planned_work_svc),
):
    planned_work.id = None
    planned_work.bonsai_id = bonsai_id
    return create_planned_work_func(planned_work=planned_work)


@router.delete("/bonsai/planned-works/{work_id}")
def delete_bonsai_planned_work(
    work_id: int,
    delete_planned_work_func: Callable = Depends(get_delete_planned_work_svc),
):
    success = delete_planned_work_func(work_id=work_id)
    if not success:
        raise HTTPException(status_code=404, detail="Planned work not found")
    return {"status": "success", "message": f"Planned work {work_id} deleted"}
