from typing import Callable
from google.adk.agents.llm_agent import Agent
from bonsai_sensei.domain.bonsai import Bonsai
from bonsai_sensei.domain.services.single_tool_call_callback import limit_to_single_tool_call
from bonsai_sensei.domain.services.garden.bonsai_tools import (
    create_get_bonsai_by_name_tool,
    create_list_bonsai_tool,
    create_list_bonsai_events_tool,
)
from bonsai_sensei.domain.services.garden.apply_fertilizer import create_apply_fertilizer_tool
from bonsai_sensei.domain.services.garden.apply_phytosanitary import create_apply_phytosanitary_tool
from bonsai_sensei.domain.services.garden.create_bonsai import create_create_bonsai_tool
from bonsai_sensei.domain.services.garden.record_transplant import create_record_transplant_tool
from bonsai_sensei.domain.services.garden.delete_bonsai import create_delete_bonsai_tool
from bonsai_sensei.domain.services.garden.update_bonsai import create_update_bonsai_tool
from bonsai_sensei.domain.services.garden.execute_planned_work import create_execute_planned_work_tool
from bonsai_sensei.domain.services.garden.add_bonsai_photo import create_add_bonsai_photo_tool
from bonsai_sensei.domain.services.garden.delete_bonsai_photo import create_delete_bonsai_photo_tool
from bonsai_sensei.domain.services.garden.list_bonsai_photos import create_list_bonsai_photos_tool
from bonsai_sensei.domain.services.cultivation.plan.planned_work_tools import create_list_planned_works_tool


GARDENER_INSTRUCTION = """
Eres el jardinero responsable de la colección de bonsáis.
Gestionas el catálogo de bonsáis (crear, actualizar, eliminar), registras eventos ya ocurridos
(fertilizaciones, tratamientos fitosanitarios, trasplantes y ejecución de trabajos planificados)
y registras fotos de bonsáis.

# Comportamiento
- Cada herramienta de confirmación gestiona sus propias validaciones. Llámala directamente con los datos del usuario; no hagas lookups previos.
- Cuando una herramienta devuelva status 'success' o 'cancelled', responde al usuario sin llamar a más herramientas.
- Si el usuario no proporciona un nombre para el bonsái, propón uno inspirado en anime o manga.
- Si falta información esencial, pídela en tu respuesta.
- Para ejecutar un trabajo planificado: usa primero list_planned_works_for_bonsai para obtener el ID, luego llama a execute_planned_work.
- Cuando el usuario envíe una foto (visible en la conversación), llama directamente a add_bonsai_photo; la herramienta mostrará la lista de bonsáis al usuario.
- Cuando el usuario quiera registrar una foto para un bonsái concreto, usa add_bonsai_photo con el bonsai_name proporcionado.
- Para consultar o listar las fotos registradas de un bonsái (sin analizarlas), usa list_bonsai_photos. Las fechas se devuelven en formato ISO (YYYY-MM-DD).
- Para eliminar una foto, usa delete_bonsai_photo con el nombre del bonsái.
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
    ask_selection: Callable,
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
    create_bonsai_photo_func: Callable[..., object] = None,
    list_bonsai_photos_func: Callable[[int], list] = None,
    delete_bonsai_photo_func: Callable[..., bool] = None,
    build_add_bonsai_photo_selection_question: Callable = None,
    build_add_bonsai_photo_confirmation: Callable = None,
    build_delete_bonsai_photo_selection_question: Callable = None,
    build_delete_bonsai_photo_confirmation: Callable = None,
    get_pending_photo_bytes: Callable = None,
    save_photo_file: Callable = None,
    clear_pending_photo: Callable = None,
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
    create_bonsai_tool = create_create_bonsai_tool(
        create_bonsai_func=create_bonsai_func,
        get_species_by_name_func=get_species_by_name_func,
        ask_confirmation=ask_confirmation,
        build_confirmation_message=build_create_bonsai_confirmation,
    )
    update_bonsai_tool = create_update_bonsai_tool(
        update_bonsai_func=update_bonsai_func,
        get_species_by_name_func=get_species_by_name_func,
        ask_confirmation=ask_confirmation,
        build_confirmation_message=build_update_bonsai_confirmation,
    )
    delete_bonsai_tool = create_delete_bonsai_tool(
        delete_bonsai_func=delete_bonsai_func,
        ask_confirmation=ask_confirmation,
        build_confirmation_message=build_delete_bonsai_confirmation,
    )
    apply_fertilizer_tool = create_apply_fertilizer_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        get_fertilizer_by_name_func=get_fertilizer_by_name_func,
        record_bonsai_event_func=record_bonsai_event_func,
        ask_confirmation=ask_confirmation,
        build_confirmation_message=build_apply_fertilizer_confirmation,
    )
    apply_fertilizer_tool.__name__ = "apply_fertilizer"
    apply_phytosanitary_tool = create_apply_phytosanitary_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        get_phytosanitary_by_name_func=get_phytosanitary_by_name_func,
        record_bonsai_event_func=record_bonsai_event_func,
        ask_confirmation=ask_confirmation,
        build_confirmation_message=build_apply_phytosanitary_confirmation,
    )
    apply_phytosanitary_tool.__name__ = "apply_phytosanitary"
    record_transplant_tool = create_record_transplant_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        record_bonsai_event_func=record_bonsai_event_func,
        ask_confirmation=ask_confirmation,
        build_confirmation_message=build_record_transplant_confirmation,
    )
    record_transplant_tool.__name__ = "record_transplant"
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
    execute_planned_work_tool = create_execute_planned_work_tool(
        get_planned_work_func=get_planned_work_func,
        record_bonsai_event_func=record_bonsai_event_func,
        delete_planned_work_func=delete_planned_work_func,
        ask_confirmation=ask_confirmation,
        build_confirmation_message=build_execute_planned_work_confirmation,
    )
    execute_planned_work_tool.__name__ = "execute_planned_work"
    add_photo_tool = create_add_bonsai_photo_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_bonsai_func=list_bonsai_func,
        create_bonsai_photo_func=create_bonsai_photo_func,
        ask_confirmation=ask_confirmation,
        ask_selection=ask_selection,
        build_selection_question=build_add_bonsai_photo_selection_question,
        build_confirmation_message=build_add_bonsai_photo_confirmation,
        get_pending_photo_bytes=get_pending_photo_bytes,
        save_photo_file=save_photo_file,
        clear_pending_photo=clear_pending_photo,
    )
    add_photo_tool.__name__ = "add_bonsai_photo"
    list_photos_tool = create_list_bonsai_photos_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_bonsai_photos_func=list_bonsai_photos_func,
    )
    list_photos_tool.__name__ = "list_bonsai_photos"
    delete_photo_tool = create_delete_bonsai_photo_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_bonsai_photos_func=list_bonsai_photos_func,
        delete_bonsai_photo_func=delete_bonsai_photo_func,
        ask_confirmation=ask_confirmation,
        ask_selection=ask_selection,
        build_selection_question=build_delete_bonsai_photo_selection_question,
        build_confirmation_message=build_delete_bonsai_photo_confirmation,
    )
    delete_photo_tool.__name__ = "delete_bonsai_photo"
    return Agent(
        model=model,
        name="gardener",
        description="Gestiona la colección de bonsáis (crear, actualizar, eliminar) y registra eventos ya ocurridos: fertilizaciones aplicadas, tratamientos fitosanitarios aplicados, trasplantes realizados, ejecución de trabajos planificados y registro de fotos. No analiza visualmente fotos ni planifica trabajos futuros.",
        instruction=GARDENER_INSTRUCTION,
        after_model_callback=limit_to_single_tool_call,
        tools=[
            list_bonsai_tool,
            get_bonsai_by_name_tool,
            create_bonsai_tool,
            update_bonsai_tool,
            delete_bonsai_tool,
            apply_fertilizer_tool,
            apply_phytosanitary_tool,
            record_transplant_tool,
            list_events_tool,
            list_works_tool,
            execute_planned_work_tool,
            add_photo_tool,
            list_photos_tool,
            delete_photo_tool,
        ],
    )
