from typing import Callable
from google.adk.agents.llm_agent import Agent
from google.adk.tools import AgentTool
from bonsai_sensei.domain.confirmation_store import ConfirmationStore
from bonsai_sensei.domain.services.cultivation.species.confirm_create_species_tool import create_confirm_create_species_tool
from bonsai_sensei.domain.services.cultivation.species.confirm_delete_species_tool import create_confirm_delete_species_tool
from bonsai_sensei.domain.services.cultivation.species.confirm_update_species_tool import create_confirm_update_species_tool
from bonsai_sensei.domain.services.cultivation.species.herbarium_tools import create_get_species_by_name_tool
from bonsai_sensei.domain.species import Species


SPECIES_INSTRUCTION = """
#ROL
Estás actuando como un botánico experto en la creación y gestión de especies de bonsáis.

# OBJETIVO
Tu objetivo es dar información sobre las especies de bonsáis registradas 
y gestionar el registro de especies.

Es muy importante que la información que proporciones sea precisa y fiable.

# INSTRUCCIONES
* Si el usuario quiere dar de alta una nueva especie de bonsái, sigue este flujo:
    - Comprueba que la especie no exista ya en el registro (por nombre común). Si ya existe, cancela la operación.
    - Si el usuario ha proporcionado el nombre científico:
        - Verifica su validez. Si no es válido, informa al usuario y cancela.
        - Solicita confirmación.
        - Una vez registrada la confirmación, informa al usuario y espera su aprobación. NO vuelvas a llamar a solicitarla.
    - Si el usuario NO ha proporcionado el nombre científico:
        - Búscalo con la herramienta de búsqueda de nombres científicos.
        - Presenta la lista de posibles nombres al usuario para que confirme cuál es el correcto.
        - Cuando el usuario confirme el nombre científico, solicita confirmación.
        - Una vez registrada la confirmación, NO vuelvas a llamar a solicitarla.
  Si el usuario solicita actualizar una especie por nombre:
    - Valida que la especie exista en el registro de especies.
    - Solicita confirmación con los datos completos de la especie a actualizar.
* Si el usuario solicita eliminar una especie por nombre:
    - Valida que la especie exista en el registro de especies.
    - Solicita confirmación con los datos completos de la especie a eliminar.
"""


def create_botanist(
    model: object,
    get_species_by_name_func: Callable[..., Species | None],
    resolve_scientific_name: Callable[..., dict],
    list_species: Callable[..., dict],
    care_guide_agent: Agent,
    create_species_func: Callable[..., Species],
    update_species_func: Callable[..., Species | None],
    delete_species_func: Callable[..., bool],
    confirmation_store: ConfirmationStore | None = None,
) -> Agent:
    get_species_by_name = create_get_species_by_name_tool(get_species_by_name_func)
    get_species_by_name.__name__ = "get_bonsai_species_by_name"
    
    care_guide_compiler = AgentTool(care_guide_agent)
    confirm_create_tool = create_confirm_create_species_tool(
        create_species_func=create_species_func,
        confirmation_store=confirmation_store,
    )
    
    confirm_update_tool = create_confirm_update_species_tool(
        update_species_func=update_species_func,
        get_species_by_name_func=get_species_by_name_func,
        confirmation_store=confirmation_store,
    )
    
    confirm_delete_tool = create_confirm_delete_species_tool(
        delete_species_func=delete_species_func,
        get_species_by_name_func=get_species_by_name_func,
        confirmation_store=confirmation_store,
    )

    return Agent(
        model=model,
        name="botanist",
        description="Un experto en botánica especializado en la gestión de especies de bonsáis.",
        instruction=SPECIES_INSTRUCTION,
        tools=[
            resolve_scientific_name,
            get_species_by_name,
            list_species,
            care_guide_compiler,
            confirm_create_tool,
            confirm_update_tool,
            confirm_delete_tool,
        ],
    )
