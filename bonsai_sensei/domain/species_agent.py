from typing import Callable
from google.adk.agents.llm_agent import Agent
from bonsai_sensei.database.species import Species
from bonsai_sensei.domain.species_tools import create_create_species_tool

SPECIES_INSTRUCTION = """
#ROL
Eres un asistente encargado de altas de especies de bonsái.

# OBJETIVO
Identifica el nombre común y la denominación científica.

# REGLAS
* Pide confirmación antes de crear la especie.
* Si el usuario confirma, llama a la herramienta create_species.
* Si el usuario rechaza, cancela la operación.
"""


def create_species_agent(model: object, create_species_func: Callable[..., Species]) -> Agent:
    create_species = create_create_species_tool(create_species_func)
    return Agent(
        model=model,
        name="species_agent",
        instruction=SPECIES_INSTRUCTION,
        tools=[create_species],
    )

