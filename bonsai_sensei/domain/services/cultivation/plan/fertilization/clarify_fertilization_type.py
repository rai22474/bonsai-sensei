from typing import Callable

from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.services.human_input import SelectionNoneResult
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call

OPTION_PUNTUAL = "Fertilización puntual"
OPTION_PLAN = "Plan de fertilización"


def create_clarify_fertilization_type_tool(
    ask_selection: Callable,
    build_question: Callable,
) -> Callable:
    @trace_tool_call
    @limit_tool_calls(agent_name="kikaru")
    async def clarify_fertilization_type(
        tool_context: ToolContext | None = None,
    ) -> str:
        """Ask the user to choose between a single fertilization event or a multi-month fertilization plan.

        Use this when the user mentions fertilization but hasn't specified whether they want a single
        application on a specific date or a recurring plan covering several months.

        Returns:
            "puntual" if the user wants a single application, "plan" if they want a period plan,
            "cancelled" if the user does not want to proceed with any fertilization action.
        """
        question = build_question()
        result = await ask_selection(
            question=question,
            options=[OPTION_PUNTUAL, OPTION_PLAN],
            tool_context=tool_context,
        )
        if isinstance(result, SelectionNoneResult):
            return "cancelled"
        return "puntual" if result == OPTION_PUNTUAL else "plan"

    return clarify_fertilization_type
