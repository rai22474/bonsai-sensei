import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from hamcrest import assert_that, equal_to, contains_string, has_key, not_, not_none

from bonsai_sensei.domain.services.shokunin import (
    Shokunin,
    _build_request,
    _is_terminal,
    _parse_plan,
    _serialize_execution,
    _sorted_steps,
)


def should_return_none_when_plan_is_missing():
    assert_that(_parse_plan(None), equal_to(None))


def should_return_none_when_plan_is_empty_string():
    assert_that(_parse_plan(""), equal_to(None))


def should_parse_dict_plan_as_is():
    plan = {"goal": "create bonsai", "steps": []}
    assert_that(_parse_plan(plan), equal_to(plan))


def should_parse_valid_json_string():
    plan = {"goal": "create bonsai", "steps": []}
    result = _parse_plan(json.dumps(plan))
    assert_that(result, equal_to(plan))


def should_return_error_string_for_invalid_json():
    result = _parse_plan("not-json-{")
    assert_that(isinstance(result, str), equal_to(True))
    assert_that(result, contains_string("Invalid action plan format"))


def should_build_request_without_parameters():
    step = {"request": "Fertilize Kaze", "parameters": {}}
    assert_that(_build_request(step), equal_to("Fertilize Kaze"))


def should_build_request_with_parameters():
    step = {"request": "Fertilize Kaze", "parameters": {"bonsai_name": "Kaze", "amount": "5ml"}}
    result = _build_request(step)
    assert_that(result, contains_string("Fertilize Kaze"))
    assert_that(result, contains_string("Parámetros:"))
    assert_that(result, contains_string("Kaze"))


def should_build_request_when_parameters_is_none():
    step = {"request": "Fertilize Kaze", "parameters": None}
    assert_that(_build_request(step), equal_to("Fertilize Kaze"))


def should_detect_cancelled_as_terminal():
    result = json.dumps({"status": "cancelled"})
    assert_that(_is_terminal(result), equal_to(True))


def should_detect_error_as_terminal():
    result = json.dumps({"status": "error", "message": "bonsai_not_found"})
    assert_that(_is_terminal(result), equal_to(True))


def should_not_detect_success_as_terminal():
    result = json.dumps({"status": "success"})
    assert_that(_is_terminal(result), equal_to(False))


def should_not_detect_plain_text_as_terminal():
    assert_that(_is_terminal("Fertilización creada correctamente"), equal_to(False))


def should_not_crash_on_invalid_json_in_terminal_check():
    assert_that(_is_terminal("not-json"), equal_to(False))


def should_sort_steps_by_order():
    plan = {"steps": [{"order": 3}, {"order": 1}, {"order": 2}]}
    result = _sorted_steps(plan)
    orders = [s["order"] for s in result]
    assert_that(orders, equal_to([1, 2, 3]))


def should_return_empty_list_when_no_steps():
    assert_that(_sorted_steps({}), equal_to([]))


def should_serialize_execution_result():
    results = [{"order": 1, "agent": "nursery", "result": "ok"}]
    serialized = _serialize_execution("create bonsai", results)
    parsed = json.loads(serialized)
    assert_that(parsed, has_key("goal"))
    assert_that(parsed, has_key("results"))
    assert_that(parsed["goal"], equal_to("create bonsai"))


@pytest.mark.asyncio
async def should_yield_error_event_when_no_plan():
    executor = _make_executor({})
    ctx = _make_ctx(action_plan=None)
    events = await executor.execute(ctx)
    assert_that(len(events), equal_to(1))
    assert_that(events[0].content.parts[0].text, contains_string("No action plan found"))


@pytest.mark.asyncio
async def should_yield_error_event_when_plan_is_invalid_json():
    executor = _make_executor({})
    ctx = _make_ctx(action_plan="not-json{")
    events = await executor.execute(ctx)
    assert_that(len(events), equal_to(1))
    assert_that(events[0].content.parts[0].text, contains_string("Invalid action plan format"))


@pytest.mark.asyncio
async def should_execute_single_step_successfully():
    tool = AsyncMock(return_value=json.dumps({"status": "success"}))
    agent_tool = _make_agent_tool(tool)
    executor = _make_executor({"nursery": agent_tool})
    plan = {"goal": "create bonsai", "steps": [{"order": 1, "agent": "nursery", "request": "Create Kaze", "parameters": {}}]}
    ctx = _make_ctx(action_plan=plan)

    events = await executor.execute(ctx)

    assert_that(len(events), equal_to(1))
    result = json.loads(events[0].content.parts[0].text)
    assert_that(result["results"][0]["agent"], equal_to("nursery"))


@pytest.mark.asyncio
async def should_stop_on_cancelled_step():
    cancelled = AsyncMock(return_value=json.dumps({"status": "cancelled"}))
    success = AsyncMock(return_value=json.dumps({"status": "success"}))
    executor = _make_executor({
        "nursery": _make_agent_tool(cancelled),
        "kikaru": _make_agent_tool(success),
    })
    plan = {
        "goal": "two steps",
        "steps": [
            {"order": 1, "agent": "nursery", "request": "Create Kaze", "parameters": {}},
            {"order": 2, "agent": "kikaru", "request": "Fertilize", "parameters": {}},
        ],
    }
    ctx = _make_ctx(action_plan=plan)

    events = await executor.execute(ctx)

    result = json.loads(events[0].content.parts[0].text)
    assert_that(len(result["results"]), equal_to(1), "Should stop after cancelled step")
    assert_that(success.called, equal_to(False), "Second step should not execute")


@pytest.mark.asyncio
async def should_stop_on_error_step():
    error = AsyncMock(return_value=json.dumps({"status": "error", "message": "bonsai_not_found"}))
    success = AsyncMock(return_value=json.dumps({"status": "success"}))
    executor = _make_executor({
        "nursery": _make_agent_tool(error),
        "kikaru": _make_agent_tool(success),
    })
    plan = {
        "goal": "two steps",
        "steps": [
            {"order": 1, "agent": "nursery", "request": "Create Kaze", "parameters": {}},
            {"order": 2, "agent": "kikaru", "request": "Fertilize", "parameters": {}},
        ],
    }
    ctx = _make_ctx(action_plan=plan)

    events = await executor.execute(ctx)

    result = json.loads(events[0].content.parts[0].text)
    assert_that(len(result["results"]), equal_to(1), "Should stop after error step")
    assert_that(success.called, equal_to(False), "Second step should not execute")


@pytest.mark.asyncio
async def should_record_error_when_agent_tool_raises():
    failing_tool = AsyncMock(side_effect=RuntimeError("connection timeout"))
    executor = _make_executor({"nursery": _make_agent_tool(failing_tool)})
    plan = {"goal": "create", "steps": [{"order": 1, "agent": "nursery", "request": "Create", "parameters": {}}]}
    ctx = _make_ctx(action_plan=plan)

    events = await executor.execute(ctx)

    result = json.loads(events[0].content.parts[0].text)
    step_result = json.loads(result["results"][0]["result"])
    assert_that(step_result["status"], equal_to("error"))
    assert_that(step_result["message"], contains_string("connection timeout"))


@pytest.mark.asyncio
async def should_record_unregistered_agent_and_continue():
    success = AsyncMock(return_value=json.dumps({"status": "success"}))
    executor = _make_executor({"kikaru": _make_agent_tool(success)})
    plan = {
        "goal": "two steps",
        "steps": [
            {"order": 1, "agent": "unknown_agent", "request": "Do something", "parameters": {}},
            {"order": 2, "agent": "kikaru", "request": "Fertilize", "parameters": {}},
        ],
    }
    ctx = _make_ctx(action_plan=plan)

    events = await executor.execute(ctx)

    result = json.loads(events[0].content.parts[0].text)
    assert_that(len(result["results"]), equal_to(2), "Both steps recorded")
    assert_that(result["results"][0]["result"], contains_string("not registered"))
    assert_that(success.called, equal_to(True), "Second step still executes")


@pytest.mark.asyncio
async def should_store_execution_result_in_session_state():
    tool = AsyncMock(return_value=json.dumps({"status": "success"}))
    executor = _make_executor({"nursery": _make_agent_tool(tool)})
    plan = {"goal": "test", "steps": [{"order": 1, "agent": "nursery", "request": "Create", "parameters": {}}]}
    ctx = _make_ctx(action_plan=plan)

    await executor.execute(ctx)

    assert_that("execution_result" in ctx.session.state, equal_to(True))


@pytest.mark.asyncio
async def should_execute_tool_step_directly():
    fn = AsyncMock(return_value={"status": "analysis_complete", "taken_on": "2025-06-01"})
    executor = _make_executor({}, callable_tools={"analyze_bonsai_photo": fn})
    plan = {"goal": "analyze", "steps": [{"order": 1, "type": "tool", "tool": "analyze_bonsai_photo", "parameters": {"bonsai_name": "Momiji", "analysis_type": "health"}}]}
    ctx = _make_ctx(action_plan=plan)

    events = await executor.execute(ctx)

    result = json.loads(events[0].content.parts[0].text)
    assert_that(result["results"][0]["tool"], equal_to("analyze_bonsai_photo"))
    assert_that(fn.called, equal_to(True))


@pytest.mark.asyncio
async def should_pass_tool_context_to_callable_tool():
    fn = AsyncMock(return_value={"status": "analysis_complete"})
    executor = _make_executor({}, callable_tools={"analyze_bonsai_photo": fn})
    plan = {"goal": "analyze", "steps": [{"order": 1, "type": "tool", "tool": "analyze_bonsai_photo", "parameters": {"bonsai_name": "Momiji", "analysis_type": "general"}}]}
    ctx = _make_ctx(action_plan=plan)

    await executor.execute(ctx)

    call_kwargs = fn.call_args.kwargs
    assert_that("tool_context" in call_kwargs, equal_to(True))


@pytest.mark.asyncio
async def should_propagate_state_delta_in_final_event():
    fn = AsyncMock(return_value={"status": "success"})
    executor = _make_executor({}, callable_tools={"analyze_bonsai_photo": fn})
    plan = {"goal": "analyze", "steps": [{"order": 1, "type": "tool", "tool": "analyze_bonsai_photo", "parameters": {}}]}
    ctx = _make_ctx(action_plan=plan)

    events = await executor.execute(ctx)

    assert_that(events[0].actions, not_none(), "Final event must carry EventActions so state_delta propagates to parent")
    assert_that("execution_result" in events[0].actions.state_delta, equal_to(True), "execution_result must be in state_delta for parent session propagation")


@pytest.mark.asyncio
async def should_record_unregistered_callable_tool_and_continue():
    fn = AsyncMock(return_value={"status": "success"})
    executor = _make_executor({}, callable_tools={"compare_bonsai_photos": fn})
    plan = {
        "goal": "two steps",
        "steps": [
            {"order": 1, "type": "tool", "tool": "unknown_tool", "parameters": {}},
            {"order": 2, "type": "tool", "tool": "compare_bonsai_photos", "parameters": {"bonsai_name": "Momiji"}},
        ],
    }
    ctx = _make_ctx(action_plan=plan)

    events = await executor.execute(ctx)

    result = json.loads(events[0].content.parts[0].text)
    assert_that(len(result["results"]), equal_to(2))
    assert_that(result["results"][0]["result"], contains_string("not registered"))
    assert_that(fn.called, equal_to(True))


def _make_executor(agent_tools: dict, callable_tools: dict = {}) -> Shokunin:
    return Shokunin(name="shokunin", description="test executor", agent_tools=agent_tools, callable_tools=callable_tools)


def _make_agent_tool(run_async_mock) -> MagicMock:
    tool = MagicMock(spec=AgentTool)
    tool.run_async = run_async_mock
    return tool


def _make_ctx(action_plan) -> MagicMock:
    session = MagicMock()
    session.state = {"action_plan": action_plan}
    ctx = MagicMock(spec=InvocationContext)
    ctx.session = session
    return ctx


# Fixtures

@pytest.fixture(autouse=True)
def patch_tool_context():
    with patch("bonsai_sensei.domain.services.shokunin.ToolContext"):
        yield


from google.adk.agents.invocation_context import InvocationContext
from google.adk.tools import AgentTool
