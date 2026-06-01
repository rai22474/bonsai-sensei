from typing import Callable

from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.services.human_input import SelectionNoneResult
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call

def create_clarify_fertilization_type_tool(
    ask_selection: Callable,
    build_question: Callable,
    build_options: Callable,
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
        options = build_options()
        result = await ask_selection(
            question=question,
            options=options,
            tool_context=tool_context,
        )
        if isinstance(result, SelectionNoneResult):
            return "cancelled"
        return "puntual" if result == options[0] else "plan"

    return clarify_fertilization_type
