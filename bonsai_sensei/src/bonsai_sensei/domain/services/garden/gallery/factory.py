import os
import re
import uuid
from datetime import date
from functools import partial
from pathlib import Path
from typing import Callable

from bonsai_sensei.domain import garden
from bonsai_sensei.domain import bonsai_photo_store
from bonsai_sensei.domain.services.garden.gallery.gallery import create_gallery


def create_gallery_group(
    model: object,
    session_factory,
    ask_confirmation: Callable,
    ask_selection: Callable,
    build_add_bonsai_photo_selection_question: Callable = None,
    build_add_bonsai_photo_confirmation: Callable = None,
    build_delete_bonsai_photo_selection_question: Callable = None,
    build_delete_bonsai_photo_confirmation: Callable = None,
    build_delete_bonsai_photo_option_label: Callable = None,
    pending_photos: dict | None = None,
):
    get_bonsai_by_name_func = partial(garden.get_bonsai_by_name, create_session=session_factory)
    list_bonsai_func = partial(garden.list_bonsai, create_session=session_factory)
    create_bonsai_photo_func = partial(bonsai_photo_store.create_bonsai_photo, create_session=session_factory)
    list_bonsai_photos_func = partial(bonsai_photo_store.list_bonsai_photos, create_session=session_factory)
    delete_bonsai_photo_func = partial(bonsai_photo_store.delete_bonsai_photo, create_session=session_factory)
    photos_root = Path(os.getenv("PHOTOS_PATH", "./photos"))
    _pending_photos = pending_photos if pending_photos is not None else {}

    def save_photo_file(bonsai_name: str, photo_bytes: bytes) -> str:
        safe_name = re.sub(r"[^\w\-]", "_", bonsai_name.lower())
        bonsai_dir = photos_root / safe_name
        bonsai_dir.mkdir(parents=True, exist_ok=True)
        file_name = f"{date.today().isoformat()}_{uuid.uuid4().hex[:8]}.webp"
        (bonsai_dir / file_name).write_bytes(photo_bytes)
        return f"{safe_name}/{file_name}"

    def get_pending_photo_bytes(user_id: str) -> bytes | None:
        return _pending_photos.get(user_id)

    def clear_pending_photo(user_id: str) -> None:
        _pending_photos.pop(user_id, None)

    return create_gallery(
        model=model,
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_bonsai_func=list_bonsai_func,
        create_bonsai_photo_func=create_bonsai_photo_func,
        list_bonsai_photos_func=list_bonsai_photos_func,
        delete_bonsai_photo_func=delete_bonsai_photo_func,
        ask_confirmation=ask_confirmation,
        ask_selection=ask_selection,
        build_add_bonsai_photo_selection_question=build_add_bonsai_photo_selection_question,
        build_add_bonsai_photo_confirmation=build_add_bonsai_photo_confirmation,
        build_delete_bonsai_photo_selection_question=build_delete_bonsai_photo_selection_question,
        build_delete_bonsai_photo_confirmation=build_delete_bonsai_photo_confirmation,
        build_delete_bonsai_photo_option_label=build_delete_bonsai_photo_option_label,
        get_pending_photo_bytes=get_pending_photo_bytes,
        save_photo_file=save_photo_file,
        clear_pending_photo=clear_pending_photo,
    )
