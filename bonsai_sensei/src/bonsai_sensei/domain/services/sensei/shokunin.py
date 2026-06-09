import json
from typing import Any, AsyncGenerator, Callable

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.adk.events.event_actions import EventActions
from google.adk.tools import AgentTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types
from pydantic import ConfigDict, Field

_TERMINAL_STATUSES = ("cancelled", "error")


class Shokunin(BaseAgent):
    """Executes mitori's action plan by calling sub-agents or tools directly, without an LLM routing layer."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    agent_tools: dict[str, AgentTool]
    callable_tools: dict[str, Callable] = {}
    create_tool_context: Callable = Field(default=ToolContext)

    async def execute(self, ctx: InvocationContext) -> list[Event]:
        plan = _parse_plan(ctx.session.state.get("action_plan"))
        if plan is None:
            return [_text_event(self.name, "No action plan found.")]
        if isinstance(plan, str):
            return [_text_event(self.name, plan)]

        event_actions = EventActions()
        tool_ctx = self.create_tool_context(invocation_context=ctx, event_actions=event_actions)
        results = await self._execute_plan(plan, tool_ctx)

        execution_result = _serialize_execution(plan.get("goal", ""), results)
        ctx.session.state["execution_result"] = execution_result
        event_actions.state_delta["execution_result"] = execution_result
        return [_text_event_with_actions(self.name, execution_result, event_actions)]

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        for event in await self.execute(ctx):
            yield event

    async def _execute_plan(
        self, plan: dict, tool_ctx: ToolContext
    ) -> list[dict]:
        results = []
        for step in _sorted_steps(plan):
            step_result = await self._execute_step(step, tool_ctx)
            results.append(step_result)
            if _is_terminal(step_result["result"]):
                break
        return results

    async def _execute_step(self, step: dict, tool_ctx: ToolContext) -> dict:
        order = step.get("order")
        step_type = step.get("type", "agent")
        if step_type == "tool":
            return await self._execute_tool_step(step, order, tool_ctx)
        return await self._execute_agent_step(step, order, tool_ctx)

    async def _execute_tool_step(self, step: dict, order: Any, tool_ctx: ToolContext) -> dict:
        tool_name = step.get("tool", "")
        fn = self.callable_tools.get(tool_name)
        if not fn:
            return {
                "order": order,
                "tool": tool_name,
                "result": f"Tool '{tool_name}' not registered in executor",
            }
        try:
            result = await fn(**step.get("parameters", {}), tool_context=tool_ctx)
            result_str = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False, default=str)
        except Exception as exc:
            result_str = json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False)
        return {"order": order, "tool": tool_name, "result": result_str}

    async def _execute_agent_step(self, step: dict, order: Any, tool_ctx: ToolContext) -> dict:
        agent_name = step.get("agent", "")
        agent_tool = self.agent_tools.get(agent_name)
        if not agent_tool:
            return {
                "order": order,
                "agent": agent_name,
                "result": f"Agent '{agent_name}' not registered in executor",
            }
        try:
            result = await agent_tool.run_async(
                args={"request": _build_request(step)},
                tool_context=tool_ctx,
            )
            result_str = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False, default=str)
        except Exception as exc:
            result_str = json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False)
        return {"order": order, "agent": agent_name, "result": result_str}


def _parse_plan(raw: object) -> dict | str | None:
    if not raw:
        return None
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return f"Invalid action plan format: {raw}"


def _sorted_steps(plan: dict) -> list[dict]:
    return sorted(plan.get("steps", []), key=lambda s: s.get("order", 0))


def _build_request(step: dict) -> str:
    request = step.get("request", "")
    parameters = step.get("parameters") or {}
    if not parameters:
        return request
    return f"{request}\nParámetros: {json.dumps(parameters, ensure_ascii=False)}"


def _is_terminal(result_str: str) -> bool:
    try:
        result = json.loads(result_str)
        return result.get("status") in _TERMINAL_STATUSES
    except (json.JSONDecodeError, AttributeError):
        return False


def _serialize_execution(goal: str, results: list[dict]) -> str:
    return json.dumps({"goal": goal, "results": results}, ensure_ascii=False)


def _text_event(author: str, text: str) -> Event:
    return Event(
        author=author,
        content=types.Content(role="model", parts=[types.Part(text=text)]),
    )


def _text_event_with_actions(author: str, text: str, actions: EventActions) -> Event:
    return Event(
        author=author,
        content=types.Content(role="model", parts=[types.Part(text=text)]),
        actions=actions,
    )
