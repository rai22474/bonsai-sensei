from typing import Callable
from google.adk.agents.llm_agent import Agent
from bonsai_sensei.domain.services.cultivation.species.create_species import create_create_species_tool
from bonsai_sensei.domain.services.single_tool_call_callback import limit_to_single_tool_call
from bonsai_sensei.domain.services.cultivation.species.delete_species import create_delete_species_tool
from bonsai_sensei.domain.services.cultivation.species.update_species import create_update_species_tool
from bonsai_sensei.domain.species import Species
from bonsai_sensei.domain.services.cultivation.species.herbarium_tools import create_search_species_tool


BOTANIST_INSTRUCTION = """
Eres el responsable del herbario de especies de bonsáis. 
Mantienes el registro actualizado: registrar nuevas especies, actualizar su información y eliminar las que ya no estén en uso. 
Cada especie tiene una ficha de cultivo en la wiki que puedes consultar con read_wiki_page.

# Comportamiento
Cuando una herramienta devuelva status 'success' o 'cancelled', responde al usuario sin llamar a más herramientas.
"""


def create_botanist(
    model: object,
    get_species_by_name_func: Callable[[str], Species | None],
    search_species_func: Callable[[str], list],
    scientific_name_resolver: Callable[[str], dict],
    wiki_page_builder: Callable[[str, str], str],
    read_wiki_page_tool: Callable,
    create_species_func: Callable[..., Species],
    update_species_func: Callable[..., Species | None],
    delete_species_func: Callable[..., bool],
    ask_confirmation: Callable,
    ask_selection: Callable,
    build_create_species_confirmation: Callable,
    build_delete_species_confirmation: Callable,
    build_update_species_confirmation: Callable,
) -> Agent:
    return Agent(
        model=model,
        name="botanist",
        description="Gestiona el catálogo de especies del herbario: registrar, actualizar y eliminar especies. Para registrar una especie solo necesita el nombre común — busca el nombre científico y genera la ficha de cultivo de forma autónoma. No requiere pasos previos de consulta. No toma decisiones de planificación ni determina fechas de cuidado.",
        instruction=BOTANIST_INSTRUCTION,
        after_model_callback=limit_to_single_tool_call,
        tools=[
            create_create_species_tool(
                create_species_func=create_species_func,
                get_species_by_name_func=get_species_by_name_func,
                scientific_name_resolver=scientific_name_resolver,
                wiki_page_builder=wiki_page_builder,
                ask_confirmation=ask_confirmation,
                ask_selection=ask_selection,
                build_confirmation_message=build_create_species_confirmation,
            ),
            create_update_species_tool(
                update_species_func=update_species_func,
                get_species_by_name_func=get_species_by_name_func,
                ask_confirmation=ask_confirmation,
                build_confirmation_message=build_update_species_confirmation,
            ),
            create_delete_species_tool(
                delete_species_func=delete_species_func,
                get_species_by_name_func=get_species_by_name_func,
                ask_confirmation=ask_confirmation,
                build_confirmation_message=build_delete_species_confirmation,
            ),
            create_search_species_tool(search_species_func=search_species_func),
            read_wiki_page_tool,
        ],
    )
