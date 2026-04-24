from typing import Callable

from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.phytosanitary import Phytosanitary
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_create_phytosanitary_tool(
    create_phytosanitary_func: Callable,
    get_phytosanitary_by_name_func: Callable[[str], Phytosanitary | None],
    wiki_page_builder: Callable[[str], tuple[str, str]],
    ask_confirmation: Callable,
    build_confirmation_message: Callable,
):
    @trace_tool_call
    @limit_tool_calls(agent_name="storekeeper")
    async def create_phytosanitary(
        name: str,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Register a new phytosanitary product and generate its wiki page after user confirmation.

        Compiles a full technical wiki page (composition, dosage, application, target pests)
        and stores the recommended amount extracted by the compiler agent.

        Args:
            name: Product name.

        Returns:
            A JSON-ready dictionary with status 'success', 'cancelled', or 'error'.
            Output JSON (success): {"status": "success", "message": "<confirmation>"}.
            Output JSON (cancelled): {"status": "cancelled", "message": "<reason>"}.
            Output JSON (error): {"status": "error", "message": "<reason>"}.
            Error reasons: "phytosanitary_name_required", "phytosanitary_already_exists".
        """
        if not name:
            return {"status": "error", "message": "phytosanitary_name_required"}

        if get_phytosanitary_by_name_func(name):
            return {"status": "error", "message": "phytosanitary_already_exists"}

        confirmed = await ask_confirmation(build_confirmation_message(name), tool_context=tool_context)

        if confirmed:
            wiki_path, recommended_amount = await wiki_page_builder(name)
            create_phytosanitary_func(
                phytosanitary=Phytosanitary(
                    name=name,
                    wiki_path=wiki_path,
                    recommended_amount=recommended_amount,
                )
            )
            return {"status": "success", "message": f"Phytosanitary product '{name}' created."}

        return {"status": "cancelled", "reason": confirmed.reason}

    return create_phytosanitary
