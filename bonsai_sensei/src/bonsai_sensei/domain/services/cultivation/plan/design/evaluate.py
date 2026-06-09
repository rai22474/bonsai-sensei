from pathlib import Path
from typing import Callable

from bonsai_sensei.domain.services.cultivation.plan.evaluate_plan import create_evaluate_plan_tool

_INSTRUCTION = """
Eres un experto en desarrollo artístico y cultivo de bonsáis. Se te proporciona el plan de desarrollo activo y nueva información relevante.
Evalúa críticamente si el plan sigue siendo adecuado a la luz de esa nueva información.

Analiza:
- ¿La nueva información afecta la salud o el vigor del árbol de forma que cambie los trabajos planificados?
- ¿Algún trabajo próximo debería posponerse, cancelarse o adelantarse?
- ¿La fase de desarrollo sigue siendo la correcta?
- ¿Es necesario replantear el plan completo?

Devuelve ÚNICAMENTE un JSON válido con este formato exacto, sin texto adicional:
{
  "verdict": "ok" | "adjust" | "replace",
  "summary": "<una o dos frases con la evaluación general>",
  "suggestions": ["<sugerencia concreta 1>", "<sugerencia concreta 2>"]
}

- "ok": el plan sigue siendo válido tal cual.
- "adjust": el plan es válido pero necesita ajustes puntuales (indica cuáles en suggestions).
- "replace": la nueva información cambia el contexto lo suficiente como para recomendar un nuevo plan.
- suggestions puede ser lista vacía si verdict es "ok".
"""

_DOCSTRING = """Evaluate the active design development plan against new information without modifying it.

Args:
    bonsai_name: Name of the bonsai whose plan to evaluate.
    new_information: New observations or events that may affect the plan (e.g. health issue, growth note, technique result).

Returns:
    A JSON-ready dict with the evaluation.
    Output JSON (success): {"status": "success", "verdict": "ok|adjust|replace", "summary": str, "suggestions": list[str]}.
    Output JSON (error): {"status": "error", "message": str}.
    Error messages: "bonsai_not_found", "no_active_plan".
"""

_TEMPLATE_DIR = Path(__file__).parent / "templates"


def create_evaluate_development_plan_tool(
    model: object,
    get_bonsai_by_name_func: Callable,
    get_active_development_plan_func: Callable,
    list_bonsai_events_func: Callable,
    read_wiki_page_func: Callable,
    list_wiki_files_func: Callable,
    ask_human: Callable,
    build_bonsai_name_question: Callable,
) -> Callable:
    return create_evaluate_plan_tool(
        tool_name="evaluate_development_plan",
        tool_docstring=_DOCSTRING,
        evaluation_instruction=_INSTRUCTION,
        template_dir=_TEMPLATE_DIR,
        model=model,
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        get_active_plan_func=get_active_development_plan_func,
        list_bonsai_events_func=list_bonsai_events_func,
        read_wiki_page_func=read_wiki_page_func,
        list_wiki_files_func=list_wiki_files_func,
        ask_human=ask_human,
        build_bonsai_name_question=build_bonsai_name_question,
    )
