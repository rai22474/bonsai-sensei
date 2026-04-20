from typing import Callable
from google.adk.agents.llm_agent import Agent
from bonsai_sensei.domain.services.cultivation.species.confirm_create_species_tool import create_confirm_create_species_tool
from bonsai_sensei.domain.services.single_tool_call_callback import limit_to_single_tool_call
from bonsai_sensei.domain.services.cultivation.species.confirm_delete_species_tool import create_confirm_delete_species_tool
from bonsai_sensei.domain.services.cultivation.species.confirm_update_species_tool import create_confirm_update_species_tool
from bonsai_sensei.domain.species import Species


BOTANIST_INSTRUCTION = """
Eres el responsable del herbario de especies de bonsáis.
Tu función es mantener el registro actualizado: registrar nuevas especies, actualizar su información y eliminar las que ya no estén en uso.
Usa las herramientas disponibles para cada operación.
"""


def create_botanist(
    model: object,
    get_species_by_name_func: Callable[[str], Species | None],
    scientific_name_resolver: Callable[[str], dict],
    care_guide_builder: Callable[[str, str], dict],
    create_species_func: Callable[..., Species],
    update_species_func: Callable[..., Species | None],
    delete_species_func: Callable[..., bool],
    ask_confirmation: Callable,
    build_create_species_confirmation: Callable,
    build_delete_species_confirmation: Callable,
    build_update_species_confirmation: Callable,
) -> Agent:
    return Agent(
        model=model,
        name="botanist",
        description="Gestiona el catálogo de especies del herbario: registrar, actualizar y eliminar especies. No toma decisiones de planificación ni determina fechas de cuidado.",
        instruction=BOTANIST_INSTRUCTION,
        after_model_callback=limit_to_single_tool_call,
        tools=[
            create_confirm_create_species_tool(
                create_species_func=create_species_func,
                get_species_by_name_func=get_species_by_name_func,
                scientific_name_resolver=scientific_name_resolver,
                care_guide_builder=care_guide_builder,
                ask_confirmation=ask_confirmation,
                build_confirmation_message=build_create_species_confirmation,
            ),
            create_confirm_update_species_tool(
                update_species_func=update_species_func,
                get_species_by_name_func=get_species_by_name_func,
                ask_confirmation=ask_confirmation,
                build_confirmation_message=build_update_species_confirmation,
            ),
            create_confirm_delete_species_tool(
                delete_species_func=delete_species_func,
                get_species_by_name_func=get_species_by_name_func,
                ask_confirmation=ask_confirmation,
                build_confirmation_message=build_delete_species_confirmation,
            ),
        ],
    )
