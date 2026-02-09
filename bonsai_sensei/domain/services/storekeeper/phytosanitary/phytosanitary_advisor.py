from typing import Callable
from google.adk.agents.llm_agent import Agent

from bonsai_sensei.domain.phytosanitary import Phytosanitary
from bonsai_sensei.domain.services.storekeeper.phytosanitary.phytosanitary_tools import (
    create_create_phytosanitary_tool,
    create_delete_phytosanitary_tool,
    create_get_phytosanitary_by_name_tool,
    create_list_phytosanitary_tool,
    create_phytosanitary_info_tool,
    create_update_phytosanitary_tool,
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
  - Muestra la información al usuario y pide aprobación explícita antes de crear.
    - Si el usuario confirma, crea el fitosanitario en el inventario sin volver a solicitar confirmación.
  - Si el usuario rechaza, cancela la operación.
* Para actualizar un fitosanitario existente:
    - Comprueba si el fitosanitario está registrado.
    - Pide confirmación antes de guardar los cambios.
    - Si el usuario confirma, actualiza los datos sin volver a solicitar confirmación.
    - Si el usuario rechaza, cancela la operación.
* Para eliminar un fitosanitario:
    - Comprueba si el fitosanitario está registrado.
    - Pide confirmación antes de eliminarlo.
    - Si el usuario confirma, elimina el fitosanitario sin volver a solicitar confirmación.
    - Si el usuario rechaza, cancela la operación.
* Cuando muestres la lista de fitosanitarios, usa los nombres exactos del inventario sin traducir ni modificar.

"""


def create_phytosanitary_storekeeper(
    model: object,
    create_phytosanitary_func: Callable[[Phytosanitary], Phytosanitary],
    update_phytosanitary_func: Callable[[str, dict], Phytosanitary | None],
    delete_phytosanitary_func: Callable[[str], bool],
    list_phytosanitary_func: Callable[[], list[Phytosanitary]],
    get_phytosanitary_by_name_func: Callable[[str], Phytosanitary | None],
    searcher: Callable[[str], dict],
) -> Agent:
    phytosanitary_info_tool = create_phytosanitary_info_tool(searcher)
    create_phytosanitary_tool = create_create_phytosanitary_tool(create_phytosanitary_func)
    update_phytosanitary_tool = create_update_phytosanitary_tool(update_phytosanitary_func)
    delete_phytosanitary_tool = create_delete_phytosanitary_tool(delete_phytosanitary_func)
    list_phytosanitary_tool = create_list_phytosanitary_tool(list_phytosanitary_func)
    get_phytosanitary_by_name_tool = create_get_phytosanitary_by_name_tool(get_phytosanitary_by_name_func)

    return Agent(
        model=model,
        name="phytosanitary_storekeeper",
        description="Gestiona productos fitosanitarios para bonsáis.",
        instruction=PHYTOSANITARY_INSTRUCTION,
        tools=[
            get_phytosanitary_by_name_tool,
            phytosanitary_info_tool,
            create_phytosanitary_tool,
            update_phytosanitary_tool,
            delete_phytosanitary_tool,
            list_phytosanitary_tool,
        ],
    )