from typing import Callable
from google.adk.agents.llm_agent import Agent
from bonsai_sensei.domain.bonsai import Bonsai
from bonsai_sensei.domain.services.bonsai.bonsai_tools import (
    create_create_bonsai_tool,
    create_delete_bonsai_tool,
    create_get_bonsai_by_name_tool,
    create_list_bonsai_tool,
    create_update_bonsai_tool,
)

GARDENER_INSTRUCTION = """
#ROL
Eres un jardinero encargado de gestionar la colección de bonsáis.

# OBJETIVO
Principalmente se encarga de saber qué bonsáis tiene el usuario en su colección. 
Que características tienen y gestionar los registros de nuevos bonsáis.

# INSTRUCCIONES
* Si el usuario quiere dar de alta un nuevo bonsái, sigue este flujo:
    - Debes validar que el nombre del bonsái no esté ya registrado. 
      Si ya existe, informa al usuario y cancela la operación.
    - Si la petición incluye el nombre del bonsái y el ID de la especie, crea el nuevo bonsái.  
    - En caso que no proporcione el nombre del bonsai inventa uno basado en animes o manga populares y proponlo al usuario.
    - Pide confirmación al usuario antes de crear el bonsái.
    - Informa al usuario del resultado de la operación, incluyendo el ID del nuevo bonsái.   
* Si falta información esencial, pide al usuario el dato que falte.
* Responde siempre en español.
"""


def create_gardener(
    model: object,
    list_bonsai_func: Callable[[], list[Bonsai]],
    create_bonsai_func: Callable[[Bonsai], Bonsai | None],
    get_bonsai_by_name_func: Callable[[str], Bonsai | None],
    update_bonsai_func: Callable[[int, dict], Bonsai | None],
    delete_bonsai_func: Callable[[int], bool],
    list_species_func: Callable[[], list],
) -> Agent:
    list_bonsai_tool = create_list_bonsai_tool(
        list_bonsai_func=list_bonsai_func,
        list_species_func=list_species_func,
    )
    list_bonsai_tool.__name__ = "list_bonsai"
    create_bonsai_tool = create_create_bonsai_tool(
        create_bonsai_func=create_bonsai_func,
        list_species_func=list_species_func,
    )
    create_bonsai_tool.__name__ = "create_bonsai"
    get_bonsai_by_name_tool = create_get_bonsai_by_name_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_species_func=list_species_func,
    )
    get_bonsai_by_name_tool.__name__ = "get_bonsai_by_name"
    update_bonsai_tool = create_update_bonsai_tool(
        update_bonsai_func=update_bonsai_func,
        list_species_func=list_species_func,
    )
    update_bonsai_tool.__name__ = "update_bonsai"
    delete_bonsai_tool = create_delete_bonsai_tool(delete_bonsai_func=delete_bonsai_func)
    delete_bonsai_tool.__name__ = "delete_bonsai"

    return Agent(
        model=model,
        name="gardener",
        description="Gestiona la colección de bonsáis y sus registros.",
        instruction=GARDENER_INSTRUCTION,
        tools=[
            list_bonsai_tool,
            create_bonsai_tool,
            get_bonsai_by_name_tool,
            update_bonsai_tool,
            delete_bonsai_tool,
        ],
    )
