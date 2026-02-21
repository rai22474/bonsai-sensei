from typing import Callable
from google.adk.agents.llm_agent import Agent

from bonsai_sensei.domain.fertilizer import Fertilizer
from bonsai_sensei.domain.confirmation_store import ConfirmationStore
from bonsai_sensei.domain.services.storekeeper.fertilizers.confirm_create_fertilizer_tool import create_confirm_create_fertilizer_tool
from bonsai_sensei.domain.services.storekeeper.fertilizers.confirm_delete_fertilizer_tool import create_confirm_delete_fertilizer_tool
from bonsai_sensei.domain.services.storekeeper.fertilizers.confirm_update_fertilizer_tool import create_confirm_update_fertilizer_tool
from bonsai_sensei.domain.services.storekeeper.fertilizers.fertilizer_tools import (
    create_get_fertilizer_by_name_tool,
    create_list_fertilizers_tool,
    create_fetch_fertilizer_info_tool,
)

FERTILIZER_INSTRUCTION = """
#ROL
Eres un experto encargado de gestionar el inventario de fertilizantes y microelementos para bonsáis con los
que cuenta el usuario para el cuidado de su colección.

# OBJETIVO
Mantener y gestionar el inventario de fertilizantes y microelementos para bonsáis,
respondiendo a las solicitudes del usuario de manera precisa y eficiente.

# INSTRUCCIONES
* En caso que el usuario solicite el alta de un nuevo producto fertilizante:
  - Comprueba si el fertilizante ya está registrado. En ese caso, informa al usuario.
  - En caso contrario, busca en internet la ficha de uso y la dosis recomendada.
  - Solicita confirmación con los datos del fertilizante.
* Para actualizar un fertilizante existente:
  - Comprueba si el fertilizante está registrado.
  - Solicita confirmación con los datos del fertilizante.
* Para eliminar un fertilizante:
  - Comprueba si el fertilizante está registrado.
  - Solicita confirmación con los datos del fertilizante.
"""


def create_fertilizer_storekeeper(
    model: object,
    list_fertilizers_func: Callable[[], list[Fertilizer]],
    get_fertilizer_by_name_func: Callable[[str], Fertilizer | None],
    searcher: Callable[[str], dict],
    create_fertilizer_func: Callable[..., Fertilizer],
    update_fertilizer_func: Callable[..., Fertilizer | None],
    delete_fertilizer_func: Callable[..., bool],
    confirmation_store: ConfirmationStore | None = None,
) -> Agent:
    fertilizer_info_tool = create_fetch_fertilizer_info_tool(searcher)
    list_fertilizers_tool = create_list_fertilizers_tool(list_fertilizers_func)
    get_fertilizer_by_name_tool = create_get_fertilizer_by_name_tool(get_fertilizer_by_name_func)
    confirm_create_tool = create_confirm_create_fertilizer_tool(
        create_fertilizer_func=create_fertilizer_func,
        confirmation_store=confirmation_store,
    )

    confirm_update_tool = create_confirm_update_fertilizer_tool(
        update_fertilizer_func=update_fertilizer_func,
        confirmation_store=confirmation_store,
    )

    confirm_delete_tool = create_confirm_delete_fertilizer_tool(
        delete_fertilizer_func=delete_fertilizer_func,
        confirmation_store=confirmation_store,
    )

    return Agent(
        model=model,
        name="fertilizer_storekeeper",
        description="Gestiona fertilizantes y microelementos para bonsáis.",
        instruction=FERTILIZER_INSTRUCTION,
        tools=[
            fertilizer_info_tool,
            list_fertilizers_tool,
            get_fertilizer_by_name_tool,
            confirm_create_tool,
            confirm_update_tool,
            confirm_delete_tool,
        ],
    )