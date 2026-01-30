from typing import Callable, List
from google.adk.agents.llm_agent import Agent

GARDENER_INSTRUCTION = """
#ROL
Eres un jardinero encargado de gestionar la colección de bonsáis.

# OBJETIVO
Mantener el registro de bonsáis, creando y consultando los ejemplares disponibles.

# INSTRUCCIONES
* Usa list_bonsai para listar los bonsáis registrados.
* Usa create_bonsai para crear nuevos bonsáis cuando el usuario lo solicite.
* Usa get_bonsai_by_name para encontrar un bonsái por su nombre.
* Si falta información esencial, pide al usuario el dato que falte.
* Responde siempre en español.
"""


def create_gardener(model: object, tools: List[Callable]) -> Agent:
    return Agent(
        model=model,
        name="gardener",
        description="Gestiona la colección de bonsáis y sus registros.",
        instruction=GARDENER_INSTRUCTION,
        tools=tools,
    )
