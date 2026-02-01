from google.adk.agents.llm_agent import Agent
from google.adk.tools import AgentTool

STOREKEEPER_INSTRUCTION = """
#ROL
Eres Storekeeper y coordinas a los agentes fertilizer_storekeeper y phytosanitary_storekeeper.

# OBJETIVO
Gestionar solicitudes relacionadas con fertilizantes y productos fitosanitarios para bonsáis.

# INSTRUCCIONES
* Usa fertilizer_storekeeper para fertilizantes y microelementos.
* Usa phytosanitary_storekeeper para fitosanitarios.
* Si no tienes suficiente información, dilo claramente.
* Responde siempre en español.
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
