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
Eres un asesor especializado en fertilizantes y microelementos para bonsáis.

# OBJETIVO
Presentar al usuario la ficha de uso y la dosis recomendada y registrar el fertilizante cuando sea aprobado.

# INSTRUCCIONES
* Usa get_fertilizer_by_name para comprobar si el fertilizante ya está registrado.
* Usa fetch_fertilizer_info para obtener la ficha de uso y la dosis recomendada.
* Muestra la información al usuario y pide aprobación explícita antes de crear.
* Si el usuario aprueba, usa create_fertilizer con los datos confirmados.
* Responde siempre en español.
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