from typing import Callable
from google.adk.agents.llm_agent import Agent
from bonsai_sensei.domain.bonsai import Bonsai
from bonsai_sensei.domain.confirmation_store import ConfirmationStore
from bonsai_sensei.domain.services.garden.bonsai_tools import (
    create_get_bonsai_by_name_tool,
    create_list_bonsai_tool,
)
from bonsai_sensei.domain.services.garden.confirm_create_bonsai_tool import create_confirm_create_bonsai_tool
from bonsai_sensei.domain.services.garden.confirm_delete_bonsai_tool import create_confirm_delete_bonsai_tool
from bonsai_sensei.domain.services.garden.confirm_update_bonsai_tool import create_confirm_update_bonsai_tool


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
    - En caso que no proporcione el nombre del bonsai inventa uno basado en animes o manga populares y proponlo al usuario.
    - Solicita confirmación, con los datos del bonsai a crear.
* Si el usuario quiere actualizar un bonsái:
    - Comprueba que el bonsái exista.
    - Solicita confirmación, con los datos del bonsai a actualizar.
* Si el usuario quiere eliminar un bonsái:
    - Comprueba que el bonsái exista.
    - Solicita confirmación, con los datos del bonsai a eliminar.
* Si falta información esencial, pide al usuario el dato que falte.
* Responde siempre en español.
"""


def create_gardener(
    model: object,
    list_bonsai_func: Callable[[], list[Bonsai]],
    get_bonsai_by_name_func: Callable[[str], Bonsai | None],
    list_species_func: Callable[[], list],
    create_bonsai_func: Callable[..., Bonsai | None],
    update_bonsai_func: Callable[..., Bonsai | None],
    delete_bonsai_func: Callable[..., bool],
    confirmation_store: ConfirmationStore | None = None,
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
        list_species_func=list_species_func,
        confirmation_store=confirmation_store,
    )
    confirm_update_tool = create_confirm_update_bonsai_tool(
        update_bonsai_func=update_bonsai_func,
        list_species_func=list_species_func,
        confirmation_store=confirmation_store,
    )
    confirm_delete_tool = create_confirm_delete_bonsai_tool(
        delete_bonsai_func=delete_bonsai_func,
        confirmation_store=confirmation_store,
    )

    return Agent(
        model=model,
        name="gardener",
        description="Gestiona la colección de bonsáis y sus registros.",
        instruction=GARDENER_INSTRUCTION,
        tools=[
            list_bonsai_tool,
            get_bonsai_by_name_tool,
            confirm_create_tool,
            confirm_update_tool,
            confirm_delete_tool,
        ],
    )
