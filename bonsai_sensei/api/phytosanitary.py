from fastapi import APIRouter, Request, HTTPException, Depends
from typing import List, Callable
from bonsai_sensei.domain.phytosanitary import Phytosanitary

router = APIRouter()


def get_list_phytosanitary_svc(request: Request) -> Callable:
    return request.app.state.phytosanitary_service["list_phytosanitary"]


def get_create_phytosanitary_svc(request: Request) -> Callable:
    return request.app.state.phytosanitary_service["create_phytosanitary"]


def get_get_phytosanitary_by_name_svc(request: Request) -> Callable:
    return request.app.state.phytosanitary_service["get_phytosanitary_by_name"]


@router.get("/phytosanitary", response_model=List[Phytosanitary])
def get_phytosanitary_list(
    list_phytosanitary: Callable = Depends(get_list_phytosanitary_svc),
):
    return list_phytosanitary()


@router.post("/phytosanitary", response_model=Phytosanitary)
def create_new_phytosanitary(
    phytosanitary: Phytosanitary,
    create_phytosanitary_func: Callable = Depends(get_create_phytosanitary_svc),
):
    phytosanitary.id = None
    return create_phytosanitary_func(phytosanitary=phytosanitary)


@router.get("/phytosanitary/{phytosanitary_name}", response_model=Phytosanitary)
def get_phytosanitary_by_name(
    phytosanitary_name: str,
    get_phytosanitary_func: Callable = Depends(get_get_phytosanitary_by_name_svc),
):
    phytosanitary = get_phytosanitary_func(name=phytosanitary_name)
    if not phytosanitary:
        raise HTTPException(status_code=404, detail="Phytosanitary not found")
    return phytosanitary
