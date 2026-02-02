from typing import Callable
from google.adk.agents.llm_agent import Agent

from bonsai_sensei.domain.fertilizer import Fertilizer
from bonsai_sensei.domain.services.storekeeper.fertilizers.fertilizer_tools import (
    create_create_fertilizer_tool,
    create_get_fertilizer_by_name_tool,
    create_list_fertilizers_tool,
    create_fertilizer_info_tool,
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
  - Si el usuario confirma, crea el fertilizante en el inventario.
  - Si el usuario rechaza, cancela la operación.
"""


def create_fertilizer_storekeeper(
    model: object,
    create_fertilizer_func: Callable[[Fertilizer], Fertilizer],
    list_fertilizers_func: Callable[[], list[Fertilizer]],
    get_fertilizer_by_name_func: Callable[[str], Fertilizer | None],
    searcher: Callable[[str], dict],
) -> Agent:
    fertilizer_info_tool = create_fertilizer_info_tool(searcher)
    fertilizer_info_tool.__name__ = "fetch_fertilizer_info"
    create_fertilizer_tool = create_create_fertilizer_tool(create_fertilizer_func)
    create_fertilizer_tool.__name__ = "create_fertilizer"
    list_fertilizers_tool = create_list_fertilizers_tool(list_fertilizers_func)
    list_fertilizers_tool.__name__ = "list_fertilizers"
    get_fertilizer_by_name_tool = create_get_fertilizer_by_name_tool(get_fertilizer_by_name_func)
    get_fertilizer_by_name_tool.__name__ = "get_fertilizer_by_name"

    return Agent(
        model=model,
        name="fertilizer_storekeeper",
        description="Gestiona fertilizantes y microelementos para bonsáis.",
        instruction=FERTILIZER_INSTRUCTION,
        tools=[
            get_fertilizer_by_name_tool,
            fertilizer_info_tool,
            create_fertilizer_tool,
            list_fertilizers_tool,
        ],
    )