from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_response import LlmResponse
from google.genai import types


def limit_to_single_tool_call(
    callback_context: CallbackContext,
    llm_response: LlmResponse,
) -> LlmResponse | None:
    """Prevent parallel tool calls by keeping only the first function call.

    When the LLM returns multiple function calls in a single response, only the
    first is kept. The agent will process subsequent calls in separate turns once
    the first completes. This avoids sending multiple confirmation requests to the
    user simultaneously.
    """
    if not (llm_response.content and llm_response.content.parts):
        return None
    function_call_parts = [
        part for part in llm_response.content.parts
        if getattr(part, "function_call", None) is not None
    ]
    if len(function_call_parts) <= 1:
        return None
    modified_content = types.Content(
        role=llm_response.content.role,
        parts=[function_call_parts[0]],
    )
    return llm_response.model_copy(update={"content": modified_content})
