from typing import Callable
from google.adk.agents.llm_agent import Agent
from bonsai_sensei.domain.bonsai import Bonsai
from bonsai_sensei.domain.services.single_tool_call_callback import limit_to_single_tool_call
from bonsai_sensei.domain.services.garden.bonsai_tools import (
    create_get_bonsai_by_name_tool,
    create_list_bonsai_tool,
    create_list_bonsai_events_tool,
)
from bonsai_sensei.domain.services.garden.confirm_apply_fertilizer_tool import create_confirm_apply_fertilizer_tool
from bonsai_sensei.domain.services.garden.confirm_apply_phytosanitary_tool import create_confirm_apply_phytosanitary_tool
from bonsai_sensei.domain.services.garden.confirm_create_bonsai_tool import create_confirm_create_bonsai_tool
from bonsai_sensei.domain.services.garden.confirm_record_transplant_tool import create_confirm_record_transplant_tool
from bonsai_sensei.domain.services.garden.confirm_delete_bonsai_tool import create_confirm_delete_bonsai_tool
from bonsai_sensei.domain.services.garden.confirm_update_bonsai_tool import create_confirm_update_bonsai_tool
from bonsai_sensei.domain.services.garden.confirm_execute_planned_work_tool import create_confirm_execute_planned_work_tool
from bonsai_sensei.domain.services.cultivation.plan.planned_work_tools import create_list_planned_works_tool


GARDENER_INSTRUCTION = """
Eres el jardinero responsable de la colección de bonsáis.

Gestionas el catálogo de bonsáis (crear, actualizar, eliminar) y registras eventos ya ocurridos (fertilizaciones, tratamientos fitosanitarios, trasplantes y ejecución de trabajos planificados).

# Normas generales
- Cada herramienta de confirmación gestiona sus propias validaciones. Llámala directamente con los datos del usuario; no hagas lookups previos.
- Cuando una herramienta devuelva status 'success' o 'cancelled', responde al usuario sin llamar a más herramientas.
- Si el usuario no proporciona un nombre para el bonsái, propón uno inspirado en anime o manga.
- Si falta información esencial, pídela en tu respuesta.
- Responde siempre en español.

# Ejecución de trabajos planificados
Para ejecutar un trabajo planificado usa primero list_planned_works_for_bonsai para obtener el ID, luego llama a confirm_execute_planned_work.
"""


def create_gardener(
    model: object,
    list_bonsai_func: Callable[[], list[Bonsai]],
    get_bonsai_by_name_func: Callable[[str], Bonsai | None],
    list_species_func: Callable[[], list],
    get_species_by_name_func: Callable[[str], object | None],
    create_bonsai_func: Callable[..., Bonsai | None],
    update_bonsai_func: Callable[..., Bonsai | None],
    delete_bonsai_func: Callable[..., bool],
    ask_confirmation: Callable,
    build_create_bonsai_confirmation: Callable,
    build_delete_bonsai_confirmation: Callable,
    build_update_bonsai_confirmation: Callable,
    build_apply_fertilizer_confirmation: Callable,
    build_apply_phytosanitary_confirmation: Callable,
    build_record_transplant_confirmation: Callable,
    build_execute_planned_work_confirmation: Callable,
    get_fertilizer_by_name_func: Callable[[str], object | None] = None,
    get_phytosanitary_by_name_func: Callable[[str], object | None] = None,
    record_bonsai_event_func: Callable[..., object] = None,
    list_bonsai_events_func: Callable[[int], list[dict]] = None,
    list_planned_works_func: Callable[..., list] = None,
    get_planned_work_func: Callable[..., object | None] = None,
    delete_planned_work_func: Callable[..., bool] = None,
) -> Agent:
    list_bonsai_tool = create_list_bonsai_tool(
        list_bonsai_func=list_bonsai_func,
        list_species_func=list_species_func,
    )
    list_bonsai_tool.__name__ = "list_bonsai"
    get_bonsai_by_name_tool = create_get_bonsai_by_name_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_species_func=list_species_func,
    )
    get_bonsai_by_name_tool.__name__ = "get_bonsai_by_name"
    confirm_create_tool = create_confirm_create_bonsai_tool(
        create_bonsai_func=create_bonsai_func,
        get_species_by_name_func=get_species_by_name_func,
        ask_confirmation=ask_confirmation,
        build_confirmation_message=build_create_bonsai_confirmation,
    )
    confirm_update_tool = create_confirm_update_bonsai_tool(
        update_bonsai_func=update_bonsai_func,
        get_species_by_name_func=get_species_by_name_func,
        ask_confirmation=ask_confirmation,
        build_confirmation_message=build_update_bonsai_confirmation,
    )
    confirm_delete_tool = create_confirm_delete_bonsai_tool(
        delete_bonsai_func=delete_bonsai_func,
        ask_confirmation=ask_confirmation,
        build_confirmation_message=build_delete_bonsai_confirmation,
    )
    confirm_apply_fertilizer_tool = create_confirm_apply_fertilizer_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        get_fertilizer_by_name_func=get_fertilizer_by_name_func,
        record_bonsai_event_func=record_bonsai_event_func,
        ask_confirmation=ask_confirmation,
        build_confirmation_message=build_apply_fertilizer_confirmation,
    )
    confirm_apply_fertilizer_tool.__name__ = "confirm_apply_fertilizer"
    confirm_apply_phytosanitary_tool = create_confirm_apply_phytosanitary_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        get_phytosanitary_by_name_func=get_phytosanitary_by_name_func,
        record_bonsai_event_func=record_bonsai_event_func,
        ask_confirmation=ask_confirmation,
        build_confirmation_message=build_apply_phytosanitary_confirmation,
    )
    confirm_apply_phytosanitary_tool.__name__ = "confirm_apply_phytosanitary"
    confirm_record_transplant_tool = create_confirm_record_transplant_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        record_bonsai_event_func=record_bonsai_event_func,
        ask_confirmation=ask_confirmation,
        build_confirmation_message=build_record_transplant_confirmation,
    )
    confirm_record_transplant_tool.__name__ = "confirm_record_transplant"
    list_events_tool = create_list_bonsai_events_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_bonsai_events_func=list_bonsai_events_func,
    )
    list_events_tool.__name__ = "list_bonsai_events"
    list_works_tool = create_list_planned_works_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_planned_works_func=list_planned_works_func,
    )
    list_works_tool.__name__ = "list_planned_works_for_bonsai"
    confirm_execute_tool = create_confirm_execute_planned_work_tool(
        get_planned_work_func=get_planned_work_func,
        record_bonsai_event_func=record_bonsai_event_func,
        delete_planned_work_func=delete_planned_work_func,
        ask_confirmation=ask_confirmation,
        build_confirmation_message=build_execute_planned_work_confirmation,
    )
    confirm_execute_tool.__name__ = "confirm_execute_planned_work"

    return Agent(
        model=model,
        name="gardener",
        description="Gestiona la colección de bonsáis (crear, actualizar, eliminar) y registra eventos ya ocurridos: fertilizaciones aplicadas, tratamientos fitosanitarios aplicados, trasplantes realizados y ejecución de trabajos planificados. No planifica trabajos futuros ni gestiona el catálogo de productos.",
        instruction=GARDENER_INSTRUCTION,
        after_model_callback=limit_to_single_tool_call,
        tools=[
            list_bonsai_tool,
            get_bonsai_by_name_tool,
            confirm_create_tool,
            confirm_update_tool,
            confirm_delete_tool,
            confirm_apply_fertilizer_tool,
            confirm_apply_phytosanitary_tool,
            confirm_record_transplant_tool,
            list_events_tool,
            list_works_tool,
            confirm_execute_tool,
        ],
    )
