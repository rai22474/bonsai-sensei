from fastapi import APIRouter, Request, HTTPException, Depends
from typing import List, Dict, Callable
from bonsai_sensei.domain.bonsai import Bonsai

router = APIRouter()


def get_list_bonsai_svc(request: Request) -> Callable:
    return request.app.state.garden_service["list_bonsai"]


def get_create_bonsai_svc(request: Request) -> Callable:
    return request.app.state.garden_service["create_bonsai"]


def get_update_bonsai_svc(request: Request) -> Callable:
    return request.app.state.garden_service["update_bonsai"]


def get_delete_bonsai_svc(request: Request) -> Callable:
    return request.app.state.garden_service["delete_bonsai"]


@router.get("/bonsai", response_model=List[Bonsai])
def get_bonsai_list(list_bonsai: Callable = Depends(get_list_bonsai_svc)):
    return list_bonsai()


@router.post("/bonsai", response_model=Bonsai)
def create_new_bonsai(
    bonsai: Bonsai,
    create_bonsai_func: Callable = Depends(get_create_bonsai_svc),
):
    bonsai.id = None
    created = create_bonsai_func(bonsai=bonsai)
    if not created:
        raise HTTPException(status_code=404, detail="Species not found")
    return created


@router.put("/bonsai/{bonsai_id}", response_model=Bonsai)
def update_existing_bonsai(
    bonsai_id: int,
    bonsai_data: Dict,
    update_bonsai_func: Callable = Depends(get_update_bonsai_svc),
):
    result = update_bonsai_func(bonsai_id=bonsai_id, bonsai_data=bonsai_data)
    if not result:
        raise HTTPException(status_code=404, detail="Bonsai or species not found")
    return result


@router.delete("/bonsai/{bonsai_id}")
def delete_existing_bonsai(
    bonsai_id: int,
    delete_bonsai_func: Callable = Depends(get_delete_bonsai_svc),
):
    success = delete_bonsai_func(bonsai_id=bonsai_id)
    if not success:
        raise HTTPException(status_code=404, detail="Bonsai not found")
    return {"status": "success", "message": f"Bonsai {bonsai_id} deleted"}
