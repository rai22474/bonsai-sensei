from typing import Callable

from bonsai_sensei.domain.services.garden.nursery.factory import create_nursery_group
from bonsai_sensei.domain.services.garden.caretaker.factory import create_caretaker_group
from bonsai_sensei.domain.services.garden.gallery.factory import create_gallery_group


def create_gardener_group(
    model: object,
    session_factory,
    ask_confirmation: Callable,
    ask_selection: Callable,
    ask_plan_review: Callable,
    build_create_bonsai_confirmation: Callable,
    build_delete_bonsai_confirmation: Callable,
    build_update_bonsai_confirmation: Callable,
    build_apply_fertilizer_confirmation: Callable,
    build_apply_phytosanitary_confirmation: Callable,
    build_record_transplant_confirmation: Callable,
    build_execute_planned_work_confirmation: Callable,
    build_execute_planned_work_selection_question: Callable,
    build_execute_planned_work_option_label: Callable,
    build_create_pest_event_confirmation: Callable,
    build_phytosanitary_plan_review_proposal: Callable,
    build_applied_treatment_question: Callable,
    build_treatment_selection_question: Callable,
    build_create_bonsai_species_selection_question: Callable = None,
    build_add_bonsai_photo_selection_question: Callable = None,
    build_add_bonsai_photo_confirmation: Callable = None,
    build_delete_bonsai_photo_selection_question: Callable = None,
    build_delete_bonsai_photo_confirmation: Callable = None,
    build_delete_bonsai_photo_option_label: Callable = None,
    pending_photos: dict | None = None,
):
    nursery = create_nursery_group(
        model=model,
        session_factory=session_factory,
        ask_confirmation=ask_confirmation,
        ask_selection=ask_selection,
        build_create_bonsai_confirmation=build_create_bonsai_confirmation,
        build_delete_bonsai_confirmation=build_delete_bonsai_confirmation,
        build_update_bonsai_confirmation=build_update_bonsai_confirmation,
        build_create_bonsai_species_selection_question=build_create_bonsai_species_selection_question,
    )
    caretaker = create_caretaker_group(
        model=model,
        session_factory=session_factory,
        ask_confirmation=ask_confirmation,
        ask_selection=ask_selection,
        ask_plan_review=ask_plan_review,
        build_apply_fertilizer_confirmation=build_apply_fertilizer_confirmation,
        build_apply_phytosanitary_confirmation=build_apply_phytosanitary_confirmation,
        build_record_transplant_confirmation=build_record_transplant_confirmation,
        build_execute_planned_work_confirmation=build_execute_planned_work_confirmation,
        build_execute_planned_work_selection_question=build_execute_planned_work_selection_question,
        build_execute_planned_work_option_label=build_execute_planned_work_option_label,
        build_create_pest_event_confirmation=build_create_pest_event_confirmation,
        build_phytosanitary_plan_review_proposal=build_phytosanitary_plan_review_proposal,
        build_applied_treatment_question=build_applied_treatment_question,
        build_treatment_selection_question=build_treatment_selection_question,
    )
    gallery = create_gallery_group(
        model=model,
        session_factory=session_factory,
        ask_confirmation=ask_confirmation,
        ask_selection=ask_selection,
        build_add_bonsai_photo_selection_question=build_add_bonsai_photo_selection_question,
        build_add_bonsai_photo_confirmation=build_add_bonsai_photo_confirmation,
        build_delete_bonsai_photo_selection_question=build_delete_bonsai_photo_selection_question,
        build_delete_bonsai_photo_confirmation=build_delete_bonsai_photo_confirmation,
        build_delete_bonsai_photo_option_label=build_delete_bonsai_photo_option_label,
        pending_photos=pending_photos,
    )
    return nursery, caretaker, gallery
