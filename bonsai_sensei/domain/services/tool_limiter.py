from functools import wraps
import hashlib
import inspect
import json
from typing import Callable
from google.adk.tools.tool_context import ToolContext


class ToolCallsLimitExceededError(RuntimeError):
    pass


DEFAULT_TOOL_PARAM_LIMIT = 3


def limit_tool_calls(
    tool: Callable | None = None,
    *,
    agent_name: str,
    limit: int | None = DEFAULT_TOOL_PARAM_LIMIT,
) -> Callable:
    if tool is None:
        def decorator(actual_tool: Callable) -> Callable:
            return _wrap_tool_calls(actual_tool, agent_name, limit)

        return decorator
    
    return _wrap_tool_calls(tool, agent_name, limit)


def _wrap_tool_calls(tool: Callable, agent_name: str, limit: int | None) -> Callable:
    if inspect.iscoroutinefunction(tool):

        @wraps(tool)
        async def wrapped(*args, **kwargs):
            _check_tool_limit(
                tool,
                agent_name,
                limit,
                _extract_tool_context(args, kwargs),
                args,
                kwargs,
            )
            return await tool(*args, **kwargs)

        return wrapped

    @wraps(tool)
    def wrapped(*args, **kwargs):
        _check_tool_limit(
            tool,
            agent_name,
            limit,
            _extract_tool_context(args, kwargs),
            args,
            kwargs,
        )
        return tool(*args, **kwargs)

    return wrapped


def _check_tool_limit(
    tool: Callable,
    agent_name: str,
    limit: int | None,
    tool_context: ToolContext | None,
    args: tuple,
    kwargs: dict,
) -> None:
    if tool_context is None:
        return
    
    counters = _get_tool_counters(tool_context)
    params_key = _build_params_key(agent_name, tool, args, kwargs)
    params_count = counters.get(params_key, 0)
    current_limit = limit if limit is not None else DEFAULT_TOOL_PARAM_LIMIT
    
    if params_count >= current_limit:
        raise ToolCallsLimitExceededError(params_key)
    
    counters[params_key] = params_count + 1


def _get_tool_counters(tool_context: ToolContext | None) -> dict[str, int]:
    if tool_context is None:
        return {}
    
    counters = tool_context.state.get("tool_call_counters")

    if not isinstance(counters, dict):
        counters = {}
        tool_context.state["tool_call_counters"] = counters
    
    return counters


def _extract_tool_context(args: tuple, kwargs: dict) -> ToolContext | None:
    tool_context = kwargs.get("tool_context")
    
    if isinstance(tool_context, ToolContext):
        return tool_context
    for value in args:
        if isinstance(value, ToolContext):
            return value
    return None


def _build_params_key(
    agent_name: str,
    tool: Callable,
    args: tuple,
    kwargs: dict,
) -> str:
    filtered_args = [value for value in args if not isinstance(value, ToolContext)]
    filtered_kwargs = {
        key: value
        for key, value in kwargs.items()
        if key != "tool_context" and not isinstance(value, ToolContext)
    }
    payload = {
        "args": filtered_args,
        "kwargs": filtered_kwargs,
    }
    try:
        signature = json.dumps(payload, default=str, sort_keys=True)
    except TypeError:
        signature = repr(payload)
    hashed_signature = hashlib.sha256(signature.encode("utf-8")).hexdigest()
    return f"{agent_name}:{tool.__name__}:params:{hashed_signature}"
