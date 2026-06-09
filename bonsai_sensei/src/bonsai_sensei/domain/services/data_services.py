from functools import partial

from bonsai_sensei.domain import garden
from bonsai_sensei.domain import herbarium
from bonsai_sensei.domain import fertilizer_catalog
from bonsai_sensei.domain import phytosanitary_registry
from bonsai_sensei.domain import bonsai_history
from bonsai_sensei.domain import user_settings_store
from bonsai_sensei.domain import cultivation_plan
from bonsai_sensei.domain import fertilization_plan_store
from bonsai_sensei.domain import phytosanitary_plan_store
from bonsai_sensei.domain import development_plan_store
from bonsai_sensei.domain import bonsai_photo_store
from bonsai_sensei.domain import pest_catalog


def create_data_services(session_factory) -> dict:
    return {
        "herbarium": {
            "list_species": partial(herbarium.list_species, create_session=session_factory),
            "search_species_by_name": partial(herbarium.search_species_by_name, create_session=session_factory),
            "get_species_by_name": partial(herbarium.get_species_by_name, create_session=session_factory),
            "create_species": partial(herbarium.create_species, create_session=session_factory),
            "update_species": partial(herbarium.update_species, create_session=session_factory),
            "delete_species": partial(herbarium.delete_species, create_session=session_factory),
        },
        "garden": {
            "list_bonsai": partial(garden.list_bonsai, create_session=session_factory),
            "create_bonsai": partial(garden.create_bonsai, create_session=session_factory),
            "get_bonsai_by_name": partial(garden.get_bonsai_by_name, create_session=session_factory),
            "update_bonsai": partial(garden.update_bonsai, create_session=session_factory),
            "delete_bonsai": partial(garden.delete_bonsai, create_session=session_factory),
        },
        "fertilizer": {
            "list_fertilizers": partial(fertilizer_catalog.list_fertilizers, create_session=session_factory),
            "create_fertilizer": partial(fertilizer_catalog.create_fertilizer, create_session=session_factory),
            "get_fertilizer_by_name": partial(fertilizer_catalog.get_fertilizer_by_name, create_session=session_factory),
            "delete_fertilizer": partial(fertilizer_catalog.delete_fertilizer, create_session=session_factory),
        },
        "phytosanitary": {
            "list_phytosanitary": partial(phytosanitary_registry.list_phytosanitary, create_session=session_factory),
            "create_phytosanitary": partial(phytosanitary_registry.create_phytosanitary, create_session=session_factory),
            "get_phytosanitary_by_name": partial(phytosanitary_registry.get_phytosanitary_by_name, create_session=session_factory),
            "delete_phytosanitary": partial(phytosanitary_registry.delete_phytosanitary, create_session=session_factory),
        },
        "bonsai_history": {
            "list_bonsai_events": partial(bonsai_history.list_bonsai_events, create_session=session_factory),
            "record_bonsai_event": partial(bonsai_history.record_bonsai_event, create_session=session_factory),
            "get_recent_unlinked_pest_events": partial(bonsai_history.get_recent_unlinked_pest_events, create_session=session_factory),
        },
        "user_settings": {
            "save_user_settings": partial(user_settings_store.save_user_settings, create_session=session_factory),
            "get_user_settings": partial(user_settings_store.get_user_settings, create_session=session_factory),
            "list_all_user_settings": partial(user_settings_store.list_all_user_settings, create_session=session_factory),
            "delete_user_settings": partial(user_settings_store.delete_user_settings, create_session=session_factory),
        },
        "cultivation_plan": {
            "list_planned_works": partial(cultivation_plan.list_planned_works, create_session=session_factory),
            "list_planned_works_in_date_range": partial(cultivation_plan.list_planned_works_in_date_range, create_session=session_factory),
            "create_planned_work": partial(cultivation_plan.create_planned_work, create_session=session_factory),
            "delete_planned_work": partial(cultivation_plan.delete_planned_work, create_session=session_factory),
        },
        "fertilization_plan": {
            "list_fertilization_plans": partial(fertilization_plan_store.list_fertilization_plans, create_session=session_factory),
            "get_fertilization_plan": partial(fertilization_plan_store.get_fertilization_plan, create_session=session_factory),
            "get_active_fertilization_plan": partial(fertilization_plan_store.get_active_fertilization_plan, create_session=session_factory),
            "create_fertilization_plan": partial(fertilization_plan_store.create_fertilization_plan, create_session=session_factory),
            "delete_fertilization_plan": partial(fertilization_plan_store.delete_fertilization_plan, create_session=session_factory),
            "get_recently_abandoned_fertilization_plans": partial(fertilization_plan_store.get_recently_abandoned_fertilization_plans, create_session=session_factory),
        },
        "phytosanitary_plan": {
            "list_phytosanitary_plans": partial(phytosanitary_plan_store.list_phytosanitary_plans, create_session=session_factory),
            "get_phytosanitary_plan": partial(phytosanitary_plan_store.get_phytosanitary_plan, create_session=session_factory),
            "get_active_phytosanitary_plan": partial(phytosanitary_plan_store.get_active_phytosanitary_plan, create_session=session_factory),
            "create_phytosanitary_plan": partial(phytosanitary_plan_store.create_phytosanitary_plan, create_session=session_factory),
            "delete_phytosanitary_plan": partial(phytosanitary_plan_store.delete_phytosanitary_plan, create_session=session_factory),
        },
        "development_plan": {
            "list_development_plans": partial(development_plan_store.list_development_plans, create_session=session_factory),
            "get_development_plan": partial(development_plan_store.get_development_plan, create_session=session_factory),
            "get_active_development_plan": partial(development_plan_store.get_active_development_plan, create_session=session_factory),
            "create_development_plan": partial(development_plan_store.create_development_plan, create_session=session_factory),
            "delete_development_plan": partial(development_plan_store.delete_development_plan, create_session=session_factory),
            "get_recently_abandoned_development_plans": partial(development_plan_store.get_recently_abandoned_development_plans, create_session=session_factory),
        },
        "bonsai_photo": {
            "create_bonsai_photo": partial(bonsai_photo_store.create_bonsai_photo, create_session=session_factory),
            "list_bonsai_photos": partial(bonsai_photo_store.list_bonsai_photos, create_session=session_factory),
            "delete_bonsai_photo": partial(bonsai_photo_store.delete_bonsai_photo, create_session=session_factory),
            "delete_bonsai_photos": partial(bonsai_photo_store.delete_bonsai_photos, create_session=session_factory),
        },
        "pest": {
            "list_pests": partial(pest_catalog.list_pests, create_session=session_factory),
            "get_pest_by_name": partial(pest_catalog.get_pest_by_name, create_session=session_factory),
            "create_pest": partial(pest_catalog.create_pest, create_session=session_factory),
            "delete_pest": partial(pest_catalog.delete_pest, create_session=session_factory),
        },
    }
