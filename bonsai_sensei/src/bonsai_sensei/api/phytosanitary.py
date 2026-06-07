from fastapi import APIRouter, Request, HTTPException, Depends, Query
from typing import List, Callable, Optional
from bonsai_sensei.domain.phytosanitary import Phytosanitary

router = APIRouter()


def get_list_phytosanitary_svc(request: Request) -> Callable:
    return request.app.state.phytosanitary_service["list_phytosanitary"]


def get_create_phytosanitary_svc(request: Request) -> Callable:
    return request.app.state.phytosanitary_service["create_phytosanitary"]


def get_get_phytosanitary_by_name_svc(request: Request) -> Callable:
    return request.app.state.phytosanitary_service["get_phytosanitary_by_name"]


def get_delete_phytosanitary_svc(request: Request) -> Callable:
    return request.app.state.phytosanitary_service["delete_phytosanitary"]


@router.get("/phytosanitary", response_model=List[Phytosanitary])
def get_phytosanitary_list(
    user_id: Optional[str] = Query(default=None),
    list_phytosanitary: Callable = Depends(get_list_phytosanitary_svc),
):
    return list_phytosanitary(user_id=user_id)


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
    user_id: Optional[str] = Query(default=None),
    get_phytosanitary_func: Callable = Depends(get_get_phytosanitary_by_name_svc),
):
    phytosanitary = get_phytosanitary_func(name=phytosanitary_name, user_id=user_id)
    if not phytosanitary:
        raise HTTPException(status_code=404, detail="Phytosanitary not found")
    return phytosanitary


@router.delete("/phytosanitary/{phytosanitary_name}")
def delete_existing_phytosanitary(
    phytosanitary_name: str,
    user_id: Optional[str] = Query(default=None),
    delete_phytosanitary_func: Callable = Depends(get_delete_phytosanitary_svc),
):
    success = delete_phytosanitary_func(name=phytosanitary_name, user_id=user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Phytosanitary not found")
    return {"status": "success", "message": f"Phytosanitary {phytosanitary_name} deleted"}
