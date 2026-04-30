from typing import Callable

from google.adk.agents.llm_agent import Agent

KANTEI_INSTRUCTION = """
Eres el kantei, experto en evaluación visual de bonsáis almacenados.
"""


def create_kantei(
    model: object,
    analyze_bonsai_photo_tool: Callable,
) -> Agent:
    return Agent(
        model=model,
        name="kantei",
        description="Evalúa visualmente fotos almacenadas de bonsáis: describe su estado agronómico y estético, diagnostica problemas y critica el diseño.",
        instruction=KANTEI_INSTRUCTION,
        tools=[analyze_bonsai_photo_tool],
    )
