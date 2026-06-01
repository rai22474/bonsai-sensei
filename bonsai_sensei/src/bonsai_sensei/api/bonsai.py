import io
import os
import uuid
from datetime import date
from pathlib import Path
from typing import List, Dict, Callable, Optional

from fastapi import APIRouter, Request, HTTPException, Depends, UploadFile, Query
from PIL import Image

from bonsai_sensei.domain.bonsai import Bonsai
from bonsai_sensei.domain.bonsai_event import BonsaiEvent
from bonsai_sensei.domain.bonsai_photo import BonsaiPhoto

router = APIRouter()

PHOTOS_PATH = os.getenv("PHOTOS_PATH", "./photos")


def get_list_bonsai_svc(request: Request) -> Callable:
    return request.app.state.garden_service["list_bonsai"]


def get_create_bonsai_svc(request: Request) -> Callable:
    return request.app.state.garden_service["create_bonsai"]


def get_update_bonsai_svc(request: Request) -> Callable:
    return request.app.state.garden_service["update_bonsai"]


def get_delete_bonsai_svc(request: Request) -> Callable:
    return request.app.state.garden_service["delete_bonsai"]


def get_list_bonsai_events_svc(request: Request) -> Callable:
    return request.app.state.bonsai_history_service["list_bonsai_events"]


def get_record_bonsai_event_svc(request: Request) -> Callable:
    return request.app.state.bonsai_history_service["record_bonsai_event"]


def get_list_bonsai_photos_svc(request: Request) -> Callable:
    return request.app.state.bonsai_photo_service["list_bonsai_photos"]


def get_create_bonsai_photo_svc(request: Request) -> Callable:
    return request.app.state.bonsai_photo_service["create_bonsai_photo"]


def get_delete_bonsai_photo_svc(request: Request) -> Callable:
    return request.app.state.bonsai_photo_service["delete_bonsai_photo"]


def get_delete_bonsai_photos_svc(request: Request) -> Callable:
    return request.app.state.bonsai_photo_service["delete_bonsai_photos"]


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


@router.get("/bonsai/{bonsai_id}/events")
def list_bonsai_events(
    bonsai_id: int,
    list_events_func: Callable = Depends(get_list_bonsai_events_svc),
):
    return list_events_func(bonsai_id=bonsai_id)


@router.post("/bonsai/{bonsai_id}/events", response_model=BonsaiEvent)
def record_bonsai_event(
    bonsai_id: int,
    event: BonsaiEvent,
    record_event_func: Callable = Depends(get_record_bonsai_event_svc),
):
    event.id = None
    event.bonsai_id = bonsai_id
    return record_event_func(bonsai_event=event)


@router.get("/bonsai/{bonsai_id}/photos", response_model=List[BonsaiPhoto])
def list_bonsai_photos(
    bonsai_id: int,
    list_photos_func: Callable = Depends(get_list_bonsai_photos_svc),
):
    return list_photos_func(bonsai_id=bonsai_id)


@router.post("/bonsai/{bonsai_id}/photos", response_model=BonsaiPhoto)
async def create_bonsai_photo(
    bonsai_id: int,
    file: UploadFile,
    create_photo_func: Callable = Depends(get_create_bonsai_photo_svc),
    taken_on: Optional[date] = Query(default=None),
):
    photos_dir = Path(PHOTOS_PATH) / str(bonsai_id)
    photos_dir.mkdir(parents=True, exist_ok=True)
    file_name = f"{uuid.uuid4().hex}.webp"
    raw_bytes = await file.read()
    image = Image.open(io.BytesIO(raw_bytes))
    image.save(photos_dir / file_name, format="WEBP", quality=85)
    photo = BonsaiPhoto(bonsai_id=bonsai_id, file_path=f"{bonsai_id}/{file_name}")
    if taken_on is not None:
        photo.taken_on = taken_on
    return create_photo_func(bonsai_photo=photo)


@router.delete("/bonsai/{bonsai_id}/photos/{photo_id}")
def delete_single_bonsai_photo(
    bonsai_id: int,
    photo_id: int,
    delete_photo_func: Callable = Depends(get_delete_bonsai_photo_svc),
):
    success = delete_photo_func(photo_id=photo_id)
    if not success:
        raise HTTPException(status_code=404, detail="Photo not found")
    return {"status": "success"}


@router.delete("/bonsai/{bonsai_id}/photos")
def delete_bonsai_photos(
    bonsai_id: int,
    list_photos_func: Callable = Depends(get_list_bonsai_photos_svc),
    delete_photos_func: Callable = Depends(get_delete_bonsai_photos_svc),
):
    photos = list_photos_func(bonsai_id=bonsai_id)
    delete_photos_func(bonsai_id=bonsai_id)
    photos_dir = Path(PHOTOS_PATH)
    for photo in photos:
        photo_file = photos_dir / photo.file_path
        if photo_file.exists():
            photo_file.unlink()
    return {"status": "success"}
