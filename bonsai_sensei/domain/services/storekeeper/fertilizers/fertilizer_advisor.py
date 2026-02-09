from typing import Callable
from google.adk.agents.llm_agent import Agent

from bonsai_sensei.domain.fertilizer import Fertilizer
from bonsai_sensei.domain.services.storekeeper.fertilizers.fertilizer_tools import (
    create_delete_fertilizer_tool,
    create_get_fertilizer_by_name_tool,
    create_list_fertilizers_tool,
    create_fertilizer_info_tool,
    create_register_fertilizer_tool,
    create_update_fertilizer_tool,
)

FERTILIZER_INSTRUCTION = """
#ROL
Eres un experto encargado de gestionar el inventario de fertilizantes y microelementos para bonsáis con los
que cuenta el usuario para el cuidado de su colección.

# OBJETIVO
Mantener y gestionar el inventario de fertilizantes y microelementos para bonsáis,
respondiendo a las solicitudes del usuario de manera precisa y eficiente.

# INSTRUCCIONES
* En caso de alta de un nuevo producto fertilizante:
  - Comprueba si el fertilizante ya está registrado. En ese caso, informa al usuario.
  - En caso contrario, busca en internet la ficha de uso y la dosis recomendada.
  - Muestra la información al usuario y pide aprobación explícita antes de crear.
  - Si el usuario confirma, registra el fertilizante en el inventario con esa información sin volver a solicitar confirmación.
    - No vuelvas a comprobar si existe después de confirmar; registra directamente.
  - Si el usuario rechaza, cancela la operación.
* Para actualizar un fertilizante existente:
    - Comprueba si el fertilizante está registrado.
    - Pide confirmación antes de guardar los cambios.
    - Si el usuario confirma, actualiza los datos sin volver a solicitar confirmación.
    - Si el usuario rechaza, cancela la operación.
* Para eliminar un fertilizante:
    - Comprueba si el fertilizante está registrado.
    - Pide confirmación antes de eliminarlo.
    - Si el usuario confirma, elimina el fertilizante sin volver a solicitar confirmación.
    - No vuelvas a comprobar si existe después de la confirmación.
    - Si el usuario rechaza, cancela la operación.
"""


def create_fertilizer_storekeeper(
    model: object,
    create_fertilizer_func: Callable[[Fertilizer], Fertilizer],
    update_fertilizer_func: Callable[[str, dict], Fertilizer | None],
    delete_fertilizer_func: Callable[[str], bool],
    list_fertilizers_func: Callable[[], list[Fertilizer]],
    get_fertilizer_by_name_func: Callable[[str], Fertilizer | None],
    searcher: Callable[[str], dict],
) -> Agent:
    fertilizer_info_tool = create_fertilizer_info_tool(searcher)
    register_fertilizer_tool = create_register_fertilizer_tool(
        searcher,
        create_fertilizer_func,
    )
    update_fertilizer_tool = create_update_fertilizer_tool(update_fertilizer_func)
    delete_fertilizer_tool = create_delete_fertilizer_tool(delete_fertilizer_func)
    list_fertilizers_tool = create_list_fertilizers_tool(list_fertilizers_func)
    get_fertilizer_by_name_tool = create_get_fertilizer_by_name_tool(get_fertilizer_by_name_func)

    return Agent(
        model=model,
        name="fertilizer_storekeeper",
        description="Gestiona fertilizantes y microelementos para bonsáis.",
        instruction=FERTILIZER_INSTRUCTION,
        tools=[
            get_fertilizer_by_name_tool,
            fertilizer_info_tool,
            register_fertilizer_tool,
            update_fertilizer_tool,
            delete_fertilizer_tool,
            list_fertilizers_tool,
        ],
    )