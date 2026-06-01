from fastapi import APIRouter, Request, HTTPException, Depends
from typing import List, Callable
from bonsai_sensei.domain.pest import Pest

router = APIRouter()


def get_list_pests_svc(request: Request) -> Callable:
    return request.app.state.pest_service["list_pests"]


def get_create_pest_svc(request: Request) -> Callable:
    return request.app.state.pest_service["create_pest"]


def get_get_pest_by_name_svc(request: Request) -> Callable:
    return request.app.state.pest_service["get_pest_by_name"]


def get_delete_pest_svc(request: Request) -> Callable:
    return request.app.state.pest_service["delete_pest"]


@router.get("/pests", response_model=List[Pest])
def get_pest_list(
    list_pests: Callable = Depends(get_list_pests_svc),
):
    return list_pests()


@router.post("/pests", response_model=Pest)
def create_new_pest(
    pest: Pest,
    create_pest_func: Callable = Depends(get_create_pest_svc),
    get_pest_func: Callable = Depends(get_get_pest_by_name_svc),
):
    pest.id = None
    existing = get_pest_func(name=pest.name)
    if existing:
        return existing
    return create_pest_func(pest=pest)


@router.get("/pests/{pest_name}", response_model=Pest)
def get_pest_by_name(
    pest_name: str,
    get_pest_func: Callable = Depends(get_get_pest_by_name_svc),
):
    pest = get_pest_func(name=pest_name)
    if not pest:
        raise HTTPException(status_code=404, detail="Pest not found")
    return pest


@router.delete("/pests/{pest_name}")
def delete_existing_pest(
    pest_name: str,
    delete_pest_func: Callable = Depends(get_delete_pest_svc),
):
    success = delete_pest_func(name=pest_name)
    if not success:
        raise HTTPException(status_code=404, detail="Pest not found")
    return {"status": "success", "message": f"Pest {pest_name} deleted"}
