import os
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
    _raw_create_bonsai_photo = partial(bonsai_photo_store.create_bonsai_photo, create_session=session_factory)
    list_bonsai_photos_func = partial(bonsai_photo_store.list_bonsai_photos, create_session=session_factory)
    photos_root = Path(os.getenv("PHOTOS_PATH", "./photos"))

    def create_bonsai_photo_func(bonsai_photo):
        flat_file = photos_root / bonsai_photo.file_path
        if flat_file.exists():
            bonsai_dir = photos_root / str(bonsai_photo.bonsai_id)
            bonsai_dir.mkdir(parents=True, exist_ok=True)
            target = bonsai_dir / Path(bonsai_photo.file_path).name
            flat_file.rename(target)
            bonsai_photo.file_path = f"{bonsai_photo.bonsai_id}/{Path(bonsai_photo.file_path).name}"
        return _raw_create_bonsai_photo(bonsai_photo=bonsai_photo)
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
        build_add_bonsai_photo_selection_question=build_add_bonsai_photo_selection_question,
        build_add_bonsai_photo_confirmation=build_add_bonsai_photo_confirmation,
    )
