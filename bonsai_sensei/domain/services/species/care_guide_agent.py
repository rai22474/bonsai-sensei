from typing import List
from pydantic import BaseModel
from google.adk.agents.llm_agent import Agent


class CareGuideRequest(BaseModel):
    common_name: str
    scientific_name: str


class CareGuideOutput(BaseModel):
    common_name: str
    scientific_name: str
    summary: str
    watering: str | None
    light: str | None
    soil: str | None
    pruning: str | None
    pests: str | None
    sources: List[str]


CARE_GUIDE_INSTRUCTION = """
#ROL
Eres un investigador de bonsáis especializado en guías de cultivo.

# OBJETIVO
Genera una guía breve y fiable con lo más relevante para el cuidado.

# INSTRUCCIONES
* Usa la herramienta build_bonsai_care_guide una sola vez y devuelve exactamente su resultado.
* Devuelve un resumen conciso y práctico.
* Incluye secciones claras para riego, luz, sustrato, poda y plagas.
* Incluye las URLs usadas en el campo sources.
* Responde siempre en español.
"""


def create_care_guide_agent(model: object, tools: list) -> Agent:
    return Agent(
        model=model,
        name="generate_bonsai_care_guide",
        description="Generates a bonsai care guide using Tavily.",
        instruction=CARE_GUIDE_INSTRUCTION,
        tools=tools,
        input_schema=CareGuideRequest,
        output_schema=CareGuideOutput,
    )
