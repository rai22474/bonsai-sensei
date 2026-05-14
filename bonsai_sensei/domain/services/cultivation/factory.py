from typing import Callable

from bonsai_sensei.domain.services.cultivation.species.factory import create_botanist_group
from bonsai_sensei.domain.services.cultivation.plan.factory import create_kikaru_group


def create_cultivation_group(
    model: object,
    session_factory,
    ask_confirmation: Callable,
    ask_human: Callable,
    ask_selection: Callable,
    ask_plan_review: Callable,
    build_fertilization_type_question: Callable,
    build_fertilization_type_options: Callable,
    build_fertilizer_confirmation: Callable,
    build_phytosanitary_confirmation: Callable,
    build_transplant_confirmation: Callable,
    build_delete_confirmation: Callable,
    build_abandon_plan_confirmation: Callable,
    build_abandon_phytosanitary_plan_confirmation: Callable,
    build_create_species_selection_question: Callable,
    build_create_species_confirmation: Callable,
    build_delete_species_confirmation: Callable,
    build_update_species_confirmation: Callable,
    build_refresh_species_wiki_confirmation: Callable,
    build_create_pest_confirmation: Callable,
    build_delete_pest_confirmation: Callable,
    orchestrator_model: object = None,
    ask_poll: Callable | None = None,
):
    botanist, weather_advisor = create_botanist_group(
        model=model,
        session_factory=session_factory,
        ask_confirmation=ask_confirmation,
        ask_selection=ask_selection,
        build_create_species_selection_question=build_create_species_selection_question,
        build_create_species_confirmation=build_create_species_confirmation,
        build_delete_species_confirmation=build_delete_species_confirmation,
        build_update_species_confirmation=build_update_species_confirmation,
        build_refresh_species_wiki_confirmation=build_refresh_species_wiki_confirmation,
        build_create_pest_confirmation=build_create_pest_confirmation,
        build_delete_pest_confirmation=build_delete_pest_confirmation,
    )
    kikaru = create_kikaru_group(
        model=model,
        session_factory=session_factory,
        ask_confirmation=ask_confirmation,
        ask_human=ask_human,
        ask_selection=ask_selection,
        ask_plan_review=ask_plan_review,
        build_fertilization_type_question=build_fertilization_type_question,
        build_fertilization_type_options=build_fertilization_type_options,
        build_fertilizer_confirmation=build_fertilizer_confirmation,
        build_phytosanitary_confirmation=build_phytosanitary_confirmation,
        build_transplant_confirmation=build_transplant_confirmation,
        build_delete_confirmation=build_delete_confirmation,
        build_abandon_plan_confirmation=build_abandon_plan_confirmation,
        build_abandon_phytosanitary_plan_confirmation=build_abandon_phytosanitary_plan_confirmation,
        orchestrator_model=orchestrator_model,
        ask_poll=ask_poll,
    )
    return botanist, weather_advisor, kikaru
