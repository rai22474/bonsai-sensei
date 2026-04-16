from typing import Callable
from google.adk.agents.llm_agent import Agent

from bonsai_sensei.domain.fertilizer import Fertilizer
from bonsai_sensei.domain.services.single_tool_call_callback import limit_to_single_tool_call
from bonsai_sensei.domain.phytosanitary import Phytosanitary
from bonsai_sensei.domain.services.storekeeper.fertilizers.confirm_create_fertilizer_tool import create_confirm_create_fertilizer_tool
from bonsai_sensei.domain.services.storekeeper.fertilizers.confirm_delete_fertilizer_tool import create_confirm_delete_fertilizer_tool
from bonsai_sensei.domain.services.storekeeper.fertilizers.confirm_update_fertilizer_tool import create_confirm_update_fertilizer_tool
from bonsai_sensei.domain.services.storekeeper.fertilizers.fertilizer_tools import create_list_fertilizers_tool
from bonsai_sensei.domain.services.storekeeper.phytosanitary.confirm_create_phytosanitary_tool import create_confirm_create_phytosanitary_tool
from bonsai_sensei.domain.services.storekeeper.phytosanitary.confirm_delete_phytosanitary_tool import create_confirm_delete_phytosanitary_tool
from bonsai_sensei.domain.services.storekeeper.phytosanitary.confirm_update_phytosanitary_tool import create_confirm_update_phytosanitary_tool
from bonsai_sensei.domain.services.storekeeper.phytosanitary.phytosanitary_tools import create_list_phytosanitary_tool

STOREKEEPER_INSTRUCTION = """
Eres el responsable del catálogo de insumos para bonsáis: fertilizantes, microelementos y productos fitosanitarios.
Tu función es mantener ambos catálogos actualizados: registrar nuevos productos, actualizar sus fichas técnicas y eliminar los que ya no se usen.
Usa las herramientas disponibles para cada operación.
"""


def create_storekeeper(
    model: object,
    list_fertilizers_func: Callable[[], list[Fertilizer]],
    get_fertilizer_by_name_func: Callable[[str], Fertilizer | None],
    fertilizer_searcher: Callable[[str], dict],
    create_fertilizer_func: Callable[..., Fertilizer],
    update_fertilizer_func: Callable[..., Fertilizer | None],
    delete_fertilizer_func: Callable[..., bool],
    list_phytosanitary_func: Callable[[], list[Phytosanitary]],
    get_phytosanitary_by_name_func: Callable[[str], Phytosanitary | None],
    phytosanitary_searcher: Callable[[str], dict],
    create_phytosanitary_func: Callable[..., Phytosanitary],
    update_phytosanitary_func: Callable[..., Phytosanitary | None],
    delete_phytosanitary_func: Callable[..., bool],
    ask_confirmation: Callable,
) -> Agent:
    return Agent(
        model=model,
        name="storekeeper",
        description="Gestiona el catálogo de fertilizantes y productos fitosanitarios para bonsáis.",
        instruction=STOREKEEPER_INSTRUCTION,
        after_model_callback=limit_to_single_tool_call,
        tools=[
            create_list_fertilizers_tool(list_fertilizers_func),
            create_confirm_create_fertilizer_tool(
                create_fertilizer_func=create_fertilizer_func,
                get_fertilizer_by_name_func=get_fertilizer_by_name_func,
                searcher=fertilizer_searcher,
                ask_confirmation=ask_confirmation,
            ),
            create_confirm_update_fertilizer_tool(
                update_fertilizer_func=update_fertilizer_func,
                get_fertilizer_by_name_func=get_fertilizer_by_name_func,
                ask_confirmation=ask_confirmation,
            ),
            create_confirm_delete_fertilizer_tool(
                delete_fertilizer_func=delete_fertilizer_func,
                get_fertilizer_by_name_func=get_fertilizer_by_name_func,
                ask_confirmation=ask_confirmation,
            ),
            create_list_phytosanitary_tool(list_phytosanitary_func),
            create_confirm_create_phytosanitary_tool(
                create_phytosanitary_func=create_phytosanitary_func,
                get_phytosanitary_by_name_func=get_phytosanitary_by_name_func,
                searcher=phytosanitary_searcher,
                ask_confirmation=ask_confirmation,
            ),
            create_confirm_update_phytosanitary_tool(
                update_phytosanitary_func=update_phytosanitary_func,
                get_phytosanitary_by_name_func=get_phytosanitary_by_name_func,
                ask_confirmation=ask_confirmation,
            ),
            create_confirm_delete_phytosanitary_tool(
                delete_phytosanitary_func=delete_phytosanitary_func,
                get_phytosanitary_by_name_func=get_phytosanitary_by_name_func,
                ask_confirmation=ask_confirmation,
            ),
        ],
    )
