from typing import Callable

from google.adk.agents.llm_agent import Agent

from bonsai_sensei.domain.services.single_tool_call_callback import limit_to_single_tool_call
from bonsai_sensei.domain.services.garden.gallery.add_bonsai_photo import create_add_bonsai_photo_tool
from bonsai_sensei.domain.services.garden.gallery.list_bonsai_photos import create_list_bonsai_photos_tool
from bonsai_sensei.domain.services.garden.gallery.delete_bonsai_photo import create_delete_bonsai_photo_tool
from bonsai_sensei.domain.services.tool_contract import TOOL_CONTRACT


GALLERY_INSTRUCTION = f"""Eres el encargado del álbum fotográfico de la colección de bonsáis.

# Comportamiento
{TOOL_CONTRACT}
- Cuando haya una foto en la conversación, regístrala directamente; la herramienta gestiona la selección del bonsái.
- Cuando el usuario quiera registrar una foto para un bonsái concreto, usa el nombre del bonsái proporcionado directamente.
- Para consultar el inventario de fotos registradas de un bonsái (sin analizarlas), usa la herramienta de listado.
- Para eliminar una foto, actúa directamente con el nombre del bonsái; la herramienta gestiona la selección y confirmación. No listes fotos antes.
"""


def create_gallery(
    model,
    get_bonsai_by_name_func: Callable,
    list_bonsai_func: Callable,
    create_bonsai_photo_func: Callable,
    list_bonsai_photos_func: Callable,
    delete_bonsai_photo_func: Callable,
    ask_confirmation: Callable,
    ask_selection: Callable,
    build_add_bonsai_photo_selection_question: Callable = None,
    build_add_bonsai_photo_confirmation: Callable = None,
    build_delete_bonsai_photo_selection_question: Callable = None,
    build_delete_bonsai_photo_confirmation: Callable = None,
    build_delete_bonsai_photo_option_label: Callable = None,
    get_pending_photo_bytes: Callable = None,
    save_photo_file: Callable = None,
    clear_pending_photo: Callable = None,
) -> Agent:
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
        build_photo_option_label=build_delete_bonsai_photo_option_label,
    )
    delete_photo_tool.__name__ = "delete_bonsai_photo"
    return Agent(
        model=model,
        name="gallery",
        description="Gestiona el álbum fotográfico de la colección: registra, lista y elimina fotos de bonsáis.",
        instruction=GALLERY_INSTRUCTION,
        after_model_callback=limit_to_single_tool_call,
        tools=[
            add_photo_tool,
            list_photos_tool,
            delete_photo_tool,
        ],
    )
