from google.adk.tools.tool_context import ToolContext


def resolve_confirmation_user_id(tool_context: ToolContext | None) -> str | None:
    if tool_context is None:
        return None
    user_id = _extract_user_id(tool_context)
    if user_id:
        return user_id
    invocation_context = getattr(tool_context, "invocation_context", None)
    user_id = _extract_user_id(invocation_context)
    if user_id:
        return user_id
    request_context = getattr(tool_context, "request_context", None)
    user_id = _extract_user_id(request_context)
    if user_id:
        return user_id
    general_context = getattr(tool_context, "context", None)
    return _extract_user_id(general_context)


def _extract_user_id(context: object | None) -> str | None:
    if context is None:
        return None
    user_id = getattr(context, "user_id", None)
    if user_id:
        return str(user_id)
    session_id = getattr(context, "session_id", None)
    if session_id:
        return str(session_id)
    return None
