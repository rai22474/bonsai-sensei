import inspect
from functools import wraps
from typing import Callable

from opentelemetry import trace

_tracer = trace.get_tracer(__name__)


def trace_tool_call(func: Callable) -> Callable:
    """Wraps a tool function with an OpenTelemetry span named tool.call.<func_name>."""
    if inspect.iscoroutinefunction(func):
        @wraps(func)
        async def wrapped(*args, **kwargs):
            with _tracer.start_as_current_span(f"tool.call.{func.__name__}"):
                return await func(*args, **kwargs)

        return wrapped

    @wraps(func)
    def wrapped(*args, **kwargs):
        with _tracer.start_as_current_span(f"tool.call.{func.__name__}"):
            return func(*args, **kwargs)

    return wrapped
