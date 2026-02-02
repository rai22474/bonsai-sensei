from typing import Callable
from google.adk.agents.llm_agent import Agent

from bonsai_sensei.domain.phytosanitary import Phytosanitary
from bonsai_sensei.domain.services.storekeeper.phytosanitary.phytosanitary_tools import (
    create_create_phytosanitary_tool,
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
  - Muestra la información al usuario y pide aprobación explícita antes de crear.
  - Si el usuario confirma, crea el fitosanitario en el inventario.
  - Si el usuario rechaza, cancela la operación.

"""


def create_phytosanitary_storekeeper(
    model: object,
    create_phytosanitary_func: Callable[[Phytosanitary], Phytosanitary],
    list_phytosanitary_func: Callable[[], list[Phytosanitary]],
    get_phytosanitary_by_name_func: Callable[[str], Phytosanitary | None],
    searcher: Callable[[str], dict],
) -> Agent:
    phytosanitary_info_tool = create_phytosanitary_info_tool(searcher)
    phytosanitary_info_tool.__name__ = "fetch_phytosanitary_info"
    create_phytosanitary_tool = create_create_phytosanitary_tool(create_phytosanitary_func)
    create_phytosanitary_tool.__name__ = "create_phytosanitary"
    list_phytosanitary_tool = create_list_phytosanitary_tool(list_phytosanitary_func)
    list_phytosanitary_tool.__name__ = "list_phytosanitary"
    get_phytosanitary_by_name_tool = create_get_phytosanitary_by_name_tool(get_phytosanitary_by_name_func)
    get_phytosanitary_by_name_tool.__name__ = "get_phytosanitary_by_name"

    return Agent(
        model=model,
        name="phytosanitary_storekeeper",
        description="Gestiona productos fitosanitarios para bonsáis.",
        instruction=PHYTOSANITARY_INSTRUCTION,
        tools=[
            get_phytosanitary_by_name_tool,
            phytosanitary_info_tool,
            create_phytosanitary_tool,
            list_phytosanitary_tool,
        ],
    )