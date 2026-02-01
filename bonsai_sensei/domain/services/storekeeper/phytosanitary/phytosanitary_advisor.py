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
Eres un asesor especializado en productos fitosanitarios para bonsáis.

# OBJETIVO
Presentar al usuario la ficha de uso y la dosis recomendada y registrar el fitosanitario cuando sea aprobado.

# INSTRUCCIONES
* Usa get_phytosanitary_by_name para comprobar si el fitosanitario ya está registrado.
* Usa fetch_phytosanitary_info para obtener la ficha de uso y la dosis recomendada.
* Muestra la información al usuario y pide aprobación explícita antes de crear.
* Si el usuario aprueba, usa create_phytosanitary con los datos confirmados.
* Responde siempre en español.
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