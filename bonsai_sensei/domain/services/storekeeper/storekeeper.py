from google.adk.agents.llm_agent import Agent
from google.adk.tools import AgentTool

STOREKEEPER_INSTRUCTION = """
#ROL
Eres el encargado de manejar en inventario de fertilizantes y fitosanitarios para bonsáis con los
que cuenta el usuario para el cuidado de su colección.

# OBJETIVO
Mantener y gestionar el inventario de fertilizantes y productos fitosanitarios para bonsáis,
respondiendo a las solicitudes del usuario de manera precisa y eficiente.

# INSTRUCCIONES
* Delega al colaborador adecuado según si la solicitud es sobre fertilizantes o fitosanitarios.
* Si no tienes suficiente información, dilo claramente.
"""


def create_storekeeper(
    model: object,
    fertilizer_storekeeper: Agent,
    phytosanitary_storekeeper: Agent,
) -> Agent:
    return Agent(
        model=model,
        name="storekeeper",
        description="Coordina fertilizantes y fitosanitarios para bonsáis.",
        instruction=STOREKEEPER_INSTRUCTION,
        tools=[
            AgentTool(fertilizer_storekeeper),
            AgentTool(phytosanitary_storekeeper),
        ],
    )
