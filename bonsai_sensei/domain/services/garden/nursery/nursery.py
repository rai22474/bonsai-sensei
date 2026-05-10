from typing import Callable

from google.adk.agents.llm_agent import Agent

from bonsai_sensei.domain.services.single_tool_call_callback import limit_to_single_tool_call
from bonsai_sensei.domain.services.garden.nursery.bonsai_tools import (
    create_get_bonsai_by_name_tool,
    create_list_bonsai_tool,
)
from bonsai_sensei.domain.services.garden.nursery.create_bonsai import create_create_bonsai_tool
from bonsai_sensei.domain.services.garden.nursery.update_bonsai import create_update_bonsai_tool
from bonsai_sensei.domain.services.garden.nursery.delete_bonsai import create_delete_bonsai_tool


NURSERY_INSTRUCTION = """Eres el encargado del registro de la colección de bonsáis.

# Comportamiento
- Para crear, actualizar o eliminar: llama directamente a la tool con los datos disponibles. Las tools gestionan internamente la confirmación.
- Cuando una herramienta devuelva status 'success' o 'cancelled', responde al usuario sin llamar a más herramientas.
- Para listar o consultar: llama directamente a la tool.
- Al mencionar nombres de bonsáis o especies en tu respuesta, escríbelos con la primera letra en mayúscula.
"""


def create_nursery(
    model,
    list_bonsai_func,
    get_bonsai_by_name_func,
    list_species_func,
    get_species_by_name_func,
    create_bonsai_func,
    update_bonsai_func,
    delete_bonsai_func,
    ask_confirmation: Callable,
    ask_selection: Callable,
    build_create_bonsai_confirmation: Callable,
    build_delete_bonsai_confirmation: Callable,
    build_update_bonsai_confirmation: Callable,
    build_create_bonsai_species_selection_question: Callable = None,
    write_wiki_page_func: Callable = None,
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
        list_species_func=list_species_func,
        get_species_by_name_func=get_species_by_name_func,
        ask_confirmation=ask_confirmation,
        ask_selection=ask_selection,
        build_selection_question=build_create_bonsai_species_selection_question,
        build_confirmation_message=build_create_bonsai_confirmation,
        write_wiki_page_func=write_wiki_page_func,
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
    return Agent(
        model=model,
        name="nursery",
        description="Gestiona el registro de la colección de bonsáis: crear, consultar, actualizar y eliminar.",
        instruction=NURSERY_INSTRUCTION,
        after_model_callback=limit_to_single_tool_call,
        tools=[
            list_bonsai_tool,
            get_bonsai_by_name_tool,
            create_bonsai_tool,
            update_bonsai_tool,
            delete_bonsai_tool,
        ],
    )
