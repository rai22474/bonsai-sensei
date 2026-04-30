import os
import re
import uuid
from datetime import date
from functools import partial
from pathlib import Path
from typing import Callable

from bonsai_sensei.domain import garden
from bonsai_sensei.domain import herbarium
from bonsai_sensei.domain import fertilizer_catalog
from bonsai_sensei.domain import phytosanitary_registry
from bonsai_sensei.domain import bonsai_history
from bonsai_sensei.domain import cultivation_plan
from bonsai_sensei.domain import bonsai_photo_store
from bonsai_sensei.domain.services.garden.gardener import create_gardener


def create_gardener_group(
    model: object,
    session_factory,
    ask_confirmation: Callable,
    ask_selection: Callable,
    build_create_bonsai_confirmation: Callable,
    build_delete_bonsai_confirmation: Callable,
    build_update_bonsai_confirmation: Callable,
    build_apply_fertilizer_confirmation: Callable,
    build_apply_phytosanitary_confirmation: Callable,
    build_record_transplant_confirmation: Callable,
    build_execute_planned_work_confirmation: Callable,
    build_add_bonsai_photo_selection_question: Callable = None,
    build_add_bonsai_photo_confirmation: Callable = None,
    build_delete_bonsai_photo_selection_question: Callable = None,
    build_delete_bonsai_photo_confirmation: Callable = None,
    pending_photos: dict | None = None,
):
    list_bonsai_func = partial(garden.list_bonsai, create_session=session_factory)
    get_bonsai_by_name_func = partial(
        garden.get_bonsai_by_name, create_session=session_factory
    )
    create_bonsai_func = partial(garden.create_bonsai, create_session=session_factory)
    update_bonsai_func = partial(garden.update_bonsai, create_session=session_factory)
    delete_bonsai_func = partial(garden.delete_bonsai, create_session=session_factory)
    list_species_func = partial(herbarium.list_species, create_session=session_factory)
    get_species_by_name_func = partial(herbarium.get_species_by_name, create_session=session_factory)
    get_fertilizer_by_name_func = partial(fertilizer_catalog.get_fertilizer_by_name, create_session=session_factory)
    get_phytosanitary_by_name_func = partial(phytosanitary_registry.get_phytosanitary_by_name, create_session=session_factory)
    record_bonsai_event_func = partial(bonsai_history.record_bonsai_event, create_session=session_factory)
    list_bonsai_events_func = partial(bonsai_history.list_bonsai_events, create_session=session_factory)
    list_planned_works_func = partial(cultivation_plan.list_planned_works, create_session=session_factory)
    get_planned_work_func = partial(cultivation_plan.get_planned_work, create_session=session_factory)
    delete_planned_work_func = partial(cultivation_plan.delete_planned_work, create_session=session_factory)
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

    def load_photo_bytes(file_path: str) -> bytes | None:
        full_path = photos_root / file_path
        if not full_path.exists():
            return None
        return full_path.read_bytes()

    return create_gardener(
        model=model,
        list_bonsai_func=list_bonsai_func,
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_species_func=list_species_func,
        get_species_by_name_func=get_species_by_name_func,
        create_bonsai_func=create_bonsai_func,
        update_bonsai_func=update_bonsai_func,
        delete_bonsai_func=delete_bonsai_func,
        get_fertilizer_by_name_func=get_fertilizer_by_name_func,
        get_phytosanitary_by_name_func=get_phytosanitary_by_name_func,
        record_bonsai_event_func=record_bonsai_event_func,
        list_bonsai_events_func=list_bonsai_events_func,
        list_planned_works_func=list_planned_works_func,
        get_planned_work_func=get_planned_work_func,
        delete_planned_work_func=delete_planned_work_func,
        ask_confirmation=ask_confirmation,
        ask_selection=ask_selection,
        build_create_bonsai_confirmation=build_create_bonsai_confirmation,
        build_delete_bonsai_confirmation=build_delete_bonsai_confirmation,
        build_update_bonsai_confirmation=build_update_bonsai_confirmation,
        build_apply_fertilizer_confirmation=build_apply_fertilizer_confirmation,
        build_apply_phytosanitary_confirmation=build_apply_phytosanitary_confirmation,
        build_record_transplant_confirmation=build_record_transplant_confirmation,
        build_execute_planned_work_confirmation=build_execute_planned_work_confirmation,
        create_bonsai_photo_func=create_bonsai_photo_func,
        list_bonsai_photos_func=list_bonsai_photos_func,
        delete_bonsai_photo_func=delete_bonsai_photo_func,
        build_add_bonsai_photo_selection_question=build_add_bonsai_photo_selection_question,
        build_add_bonsai_photo_confirmation=build_add_bonsai_photo_confirmation,
        build_delete_bonsai_photo_selection_question=build_delete_bonsai_photo_selection_question,
        build_delete_bonsai_photo_confirmation=build_delete_bonsai_photo_confirmation,
        get_pending_photo_bytes=get_pending_photo_bytes,
        save_photo_file=save_photo_file,
        clear_pending_photo=clear_pending_photo,
    )
