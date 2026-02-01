from fastapi import APIRouter, Request, HTTPException, Depends
from typing import List, Callable
from bonsai_sensei.domain.fertilizer import Fertilizer

router = APIRouter()


def get_list_fertilizers_svc(request: Request) -> Callable:
    return request.app.state.fertilizer_service["list_fertilizers"]


def get_create_fertilizer_svc(request: Request) -> Callable:
    return request.app.state.fertilizer_service["create_fertilizer"]


def get_get_fertilizer_by_name_svc(request: Request) -> Callable:
    return request.app.state.fertilizer_service["get_fertilizer_by_name"]


@router.get("/fertilizers", response_model=List[Fertilizer])
def get_fertilizers_list(list_fertilizers: Callable = Depends(get_list_fertilizers_svc)):
    return list_fertilizers()


@router.post("/fertilizers", response_model=Fertilizer)
def create_new_fertilizer(
    fertilizer: Fertilizer,
    create_fertilizer_func: Callable = Depends(get_create_fertilizer_svc),
):
    fertilizer.id = None
    return create_fertilizer_func(fertilizer=fertilizer)


@router.get("/fertilizers/{fertilizer_name}", response_model=Fertilizer)
def get_fertilizer_by_name(
    fertilizer_name: str,
    get_fertilizer_func: Callable = Depends(get_get_fertilizer_by_name_svc),
):
    fertilizer = get_fertilizer_func(name=fertilizer_name)
    if not fertilizer:
        raise HTTPException(status_code=404, detail="Fertilizer not found")
    return fertilizer