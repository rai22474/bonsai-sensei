from typing import Callable
from google.adk.agents.llm_agent import Agent
from bonsai_sensei.domain.services.cultivation.species.create_species import create_create_species_tool
from bonsai_sensei.domain.services.cultivation.species.delete_species import create_delete_species_tool
from bonsai_sensei.domain.services.cultivation.species.update_species import create_update_species_tool
from bonsai_sensei.domain.services.cultivation.species.refresh_species_wiki import create_refresh_species_wiki_tool
from bonsai_sensei.domain.services.cultivation.species.herbarium_tools import create_search_species_tool
from bonsai_sensei.domain.services.cultivation.pests.pest_tools import create_list_pests_tool, create_get_pest_by_name_tool
from bonsai_sensei.domain.services.cultivation.pests.create_pest import create_create_pest_tool
from bonsai_sensei.domain.services.cultivation.pests.delete_pest import create_delete_pest_tool
from bonsai_sensei.domain.services.single_tool_call_callback import limit_to_single_tool_call
from bonsai_sensei.domain.species import Species


BOTANIST_INSTRUCTION = """
Eres el responsable del herbario de especies de bonsáis.
Mantienes el registro actualizado: registrar nuevas especies, actualizar su información y eliminar las que ya no estén en uso.
Cada especie tiene una ficha de cultivo en la wiki que puedes consultar con read_wiki_page.

# Comportamiento
- Cuando una herramienta devuelva status 'success' o 'cancelled', responde al usuario sin llamar a más herramientas.
- Al mencionar nombres de especies en tu respuesta, escríbelos con la primera letra en mayúscula.
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
    list_pests_func: Callable,
    get_pest_by_name_func: Callable,
    create_pest_func: Callable,
    delete_pest_func: Callable,
    compile_pest_page: Callable,
    ask_confirmation: Callable,
    ask_selection: Callable,
    build_create_species_selection_question: Callable,
    build_create_species_confirmation: Callable,
    build_delete_species_confirmation: Callable,
    build_update_species_confirmation: Callable,
    build_refresh_species_wiki_confirmation: Callable,
    build_create_pest_confirmation: Callable,
    build_delete_pest_confirmation: Callable,
    refresh_species_wiki_tool: Callable,
    post_create_species_hook: Callable[[str], None] | None = None,
) -> Agent:
    return Agent(
        model=model,
        name="botanist",
        description="Gestiona el catálogo de especies del herbario y el catálogo de plagas: registrar, actualizar y eliminar especies; registrar, listar y eliminar plagas del catálogo. Para registrar una especie solo necesita el nombre común — busca el nombre científico y genera la ficha de cultivo de forma autónoma. No requiere pasos previos de consulta. No toma decisiones de planificación ni determina fechas de cuidado. No debe invocarse como paso previo a la creación de bonsáis — el nursery gestiona la validación de especies internamente.",
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
                build_selection_question=build_create_species_selection_question,
                build_confirmation_message=build_create_species_confirmation,
                post_create_hook=post_create_species_hook,
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
            refresh_species_wiki_tool,
            read_wiki_page_tool,
            create_list_pests_tool(list_pests_func=list_pests_func),
            create_get_pest_by_name_tool(get_pest_by_name_func=get_pest_by_name_func),
            create_create_pest_tool(
                create_pest_func=create_pest_func,
                get_pest_by_name_func=get_pest_by_name_func,
                wiki_page_builder=compile_pest_page,
                ask_confirmation=ask_confirmation,
                build_confirmation_message=build_create_pest_confirmation,
            ),
            create_delete_pest_tool(
                delete_pest_func=delete_pest_func,
                get_pest_by_name_func=get_pest_by_name_func,
                ask_confirmation=ask_confirmation,
                build_confirmation_message=build_delete_pest_confirmation,
            ),
        ],
    )
