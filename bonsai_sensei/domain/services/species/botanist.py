from typing import Callable
from google.adk.agents.llm_agent import Agent
from google.adk.tools import AgentTool
from bonsai_sensei.database.species import Species
from bonsai_sensei.domain.services.species.herbarium_tools import (
    create_species_tool,
    create_delete_bonsai_species_tool,
    create_update_bonsai_species_tool,
)

SPECIES_INSTRUCTION = """
#ROL
Estás actuando como un botánico experto en la creación y gestión de especies de bonsáis.

# OBJETIVO
Tu objetivo es dar información sobre las especies de bonsáis registradas 
y gestionar las especies que el usuario tenga en su colección de bonsáis.

Es muy importante que la información que proporciones sea precisa y fiable.

# INSTRUCCIONES
* Si el usuario quiere dar de alta una nueva especie de bonsái, sigue este flujo:
    - Debes validar que la especie no exista ya en la base de datos usando list_bonsai_species. 
      Si ya existe, informa al usuario y cancela la operación.
  - En caso que llegue el nombre científico, debes verificar su validez usando resolve_bonsai_scientific_names.
  - En caso que el nombre científico no sea válido, informa al usuario y procede como si no se hubiera proporcionado.
  - En caso solo llegue un nombre común, busca su nombre científico usando resolve_bonsai_scientific_names.
  - Devuelve la lista de posibles nombres científicos encontrados al usuario para que confirme cuál es el correcto.
  - Pide confirmación al usuario antes de crear la especie.
  - Si el usuario confirma, usa generate_bonsai_care_guide y luego llama a create_bonsai_species con el nombre científico.
  - Si el usuario rechaza, cancela la operación.  
"""


def create_botanist(
    model: object,
    create_species_func: Callable[..., Species],
    update_species_func: Callable[..., Species | None],
    delete_species_func: Callable[..., bool],
    resolve_scientific_name: Callable[..., dict],
    list_species: Callable[..., dict],
    care_guide_agent: Agent,
) -> Agent:
    create_species = create_species_tool(create_species_func)
    create_species.__name__ = "create_bonsai_species"
    update_species = create_update_bonsai_species_tool(update_species_func)
    update_species.__name__ = "update_bonsai_species"
    delete_species = create_delete_bonsai_species_tool(delete_species_func)
    delete_species.__name__ = "delete_bonsai_species"
    care_guide_compiler = AgentTool(care_guide_agent)

    return Agent(
        model=model,
        name="botanist",
        description="Un experto en botánica especializado en la gestión de especies de bonsáis.",
        instruction=SPECIES_INSTRUCTION,
        tools=[
            resolve_scientific_name,
            create_species,
            update_species,
            delete_species,
            list_species,
            care_guide_compiler,
        ],
    )
