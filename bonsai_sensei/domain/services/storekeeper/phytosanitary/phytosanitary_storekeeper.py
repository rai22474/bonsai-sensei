from typing import Callable
from google.adk.agents.llm_agent import Agent

from bonsai_sensei.domain.phytosanitary import Phytosanitary
from bonsai_sensei.domain.confirmation import Confirmation
from bonsai_sensei.domain.confirmation_store import ConfirmationStore
from bonsai_sensei.domain.services.storekeeper.phytosanitary.confirm_create_phytosanitary_tool import create_confirm_create_phytosanitary_tool
from bonsai_sensei.domain.services.storekeeper.phytosanitary.confirm_delete_phytosanitary_tool import create_confirm_delete_phytosanitary_tool
from bonsai_sensei.domain.services.storekeeper.phytosanitary.confirm_update_phytosanitary_tool import create_confirm_update_phytosanitary_tool
from bonsai_sensei.domain.services.storekeeper.phytosanitary.phytosanitary_tools import (
    create_get_phytosanitary_by_name_tool,
    create_list_phytosanitary_tool,
    create_phytosanitary_info_tool,
)

PHYTOSANITARY_INSTRUCTION = """
#ROL
Eres un experto encargado de gestionar el inventario de fitosanitarios para bonsáis con los
que cuenta el usuario para el cuidado de su colección.

# OBJETIVO
Mantener y gestionar el inventario de fitosanitarios para bonsáis,
respondiendo a las solicitudes del usuario de manera precisa y eficiente.

# INSTRUCCIONES
* En caso de alta de un nuevo producto fitosanitario:
  - Comprueba si el fitosanitario ya está registrado. En ese caso, informa al usuario.
  - En caso contrario, busca en internet la ficha de uso y la dosis recomendada.
  - Guarda siempre a que plaga o enfermedad va dirigido el fitosanitario.
  - Solicita confirmación con register_confirmation_command usando action=create_phytosanitary y action_args con los datos del fitosanitario.
* Para actualizar un fitosanitario existente:
    - Comprueba si el fitosanitario está registrado.
    - Solicita confirmación con register_confirmation_command usando action=update_phytosanitary y action_args con el nombre y los cambios.
* Para eliminar un fitosanitario:
    - Comprueba si el fitosanitario está registrado.
    - Solicita confirmación con register_confirmation_command usando action=delete_phytosanitary y action_args con el nombre.
* Cuando muestres la lista de fitosanitarios, usa los nombres exactos del inventario sin traducir ni modificar.

"""


def create_phytosanitary_storekeeper(
    model: object,
    list_phytosanitary_func: Callable[[], list[Phytosanitary]],
    get_phytosanitary_by_name_func: Callable[[str], Phytosanitary | None],
    searcher: Callable[[str], dict],
    create_phytosanitary_func: Callable[..., Phytosanitary],
    update_phytosanitary_func: Callable[..., Phytosanitary | None],
    delete_phytosanitary_func: Callable[..., bool],
    confirmation_store: ConfirmationStore | None = None
) -> Agent:
    phytosanitary_info_tool = create_phytosanitary_info_tool(searcher)
    list_phytosanitary_tool = create_list_phytosanitary_tool(list_phytosanitary_func)
    get_phytosanitary_by_name_tool = create_get_phytosanitary_by_name_tool(
        get_phytosanitary_by_name_func
    )

    confirm_create_tool = create_confirm_create_phytosanitary_tool(
        create_phytosanitary_func=create_phytosanitary_func,
        confirmation_store=confirmation_store,
    )

    confirm_update_tool = create_confirm_update_phytosanitary_tool(
        update_phytosanitary_func=update_phytosanitary_func,
        confirmation_store=confirmation_store,
    )

    confirm_delete_tool = create_confirm_delete_phytosanitary_tool(
        delete_phytosanitary_func=delete_phytosanitary_func,
        confirmation_store=confirmation_store,
    )

    return Agent(
        model=model,
        name="phytosanitary_storekeeper",
        description="Un experto en fitosanitarios especializado en la gestión de inventarios de bonsáis.",
        instruction=PHYTOSANITARY_INSTRUCTION,
        tools=[
            phytosanitary_info_tool,
            list_phytosanitary_tool,
            get_phytosanitary_by_name_tool,
            confirm_create_tool,
            confirm_update_tool,
            confirm_delete_tool,
        ],
    )
