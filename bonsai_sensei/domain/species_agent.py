from typing import Callable
from google.adk.agents.llm_agent import Agent
from bonsai_sensei.database.species import Species
from bonsai_sensei.domain.species_tools import create_create_species_tool

SPECIES_INSTRUCTION = """
#ROL
Eres un asistente encargado de altas de especies de bonsái.

# OBJETIVO
Tu objetivo es ayudar a los usuarios a identificar y crear especies de bonsái. 
Es una muy importante ya que de la correcta identificación de la especie depende el éxito en su cuidado.


# INSTRUCCIONES
* El usuario muestra un interés en dar de alta una nueva especie de bonsái, proporcionando su nombre común. 
 Puede proporcionar también el nombre científico si lo conoce. Pero no es siempre el caso.
* Debes validar que la la especie no exista ya en la base de datos antes de proceder usando la herramienta get_garden_species. Si ya existe, informa al usuario y cancela la operación. 
* En caso que llegue el nombre científico, debes verificar su validez usando la herramienta de resolución de nombres científicos.
* En caso que el nombre científico no sea válido, informa al usuario y procede como si no se hubiera proporcionado.
* En caso se solo llegue un nombre común, busca su nombre científico usando la herramienta de resolución de nombres científicos.
  Devuelve la lista de posibles nombres científicos encontrados al usuario para que confirme cuál es el correcto.
* Pide confirmación al usuario antes de crear la especie.
* Si el usuario confirma, llama a create_species con el nombre científico.
* Si el usuario rechaza, cancela la operación.
"""


def create_species_agent(
    model: object,
    create_species_func: Callable[..., Species],
    resolve_scientific_name: Callable[..., dict],
    list_species: Callable[..., dict],
) -> Agent:
    create_species = create_create_species_tool(create_species_func)
    return Agent(
        model=model,
        name="species_agent",
        instruction=SPECIES_INSTRUCTION,
        tools=[resolve_scientific_name, list_species, create_species],
    )

