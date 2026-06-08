import uuid
from dataclasses import dataclass
from typing import Callable, Literal

from google.adk.agents.llm_agent import LlmAgent
from google.adk.events.request_input import RequestInput
from google.adk.runners import InMemoryRunner, RunConfig
from google.adk.workflow import START, Workflow, node
from google.adk.workflow.utils._workflow_hitl_utils import (
    create_request_input_response,
    get_request_input_interrupt_ids,
    has_request_input_function_call,
)
from google.genai import types
from pydantic import BaseModel

_CLARIFY_INTERRUPT_ID = "clarification-input"
_MAX_LLM_CALLS_PER_TURN = 5


class ClarificationAction(BaseModel):
    action: Literal["ask", "ask_poll", "done", "cancel"]
    question: str = ""
    options: list[str] = []
    objectives: str = ""
    preferences: str = ""
    context: str = ""


@dataclass
class _RequestInputDetails:
    interrupt_id: str
    message: str
    options: list[str]
    is_poll: bool


def create_clarification_loop_runner(
    model: object, ask_human: Callable, app_name: str, ask_poll: Callable | None = None
) -> Callable:
    async def run_clarification_loop(rendered_prompt: str, outer_tool_context) -> dict:

        @node(rerun_on_resume=True)
        async def clarify(ctx):
            resume = (ctx.resume_inputs or {}).get(_CLARIFY_INTERRUPT_ID)
            if resume is not None:
                _accumulate_user_answer(ctx, resume if isinstance(resume, dict) else {"result": resume})

            history = ctx.state.get("qa_history", [])
            prompt_with_history = rendered_prompt + _build_history_section(history)
            action = await _ask_clarifier_llm(model, prompt_with_history)

            if action.action in ("done", "cancel"):
                _store_clarification_result(ctx, action)
                return

            ctx.state["pending_question"] = action.question
            yield RequestInput(
                interrupt_id=_CLARIFY_INTERRUPT_ID,
                message=action.question,
                payload={"options": action.options, "is_poll": action.action == "ask_poll"},
            )

        async def _ask_user(ri: _RequestInputDetails) -> str:
            if ri.is_poll and ask_poll is not None and ri.options:
                return await ask_poll(ri.message, ri.options, tool_context=outer_tool_context)
            return await ask_human(ri.message, tool_context=outer_tool_context)

        async def _run_workflow_until_complete(outer_runner, session_id) -> None:
            cur_msg = types.Content(role="user", parts=[types.Part(text="begin")])
            while True:
                request_input = None
                async for event in outer_runner.run_async(
                    user_id=outer_runner.app_name,
                    session_id=session_id,
                    new_message=cur_msg,
                ):
                    request_input = _extract_request_input(event) or request_input

                if request_input is None:
                    break

                user_response = await _ask_user(request_input)
                cur_msg = types.Content(
                    role="user",
                    parts=[create_request_input_response(request_input.interrupt_id, {"result": user_response})],
                )

        wf = Workflow(name=f"{app_name}_wf", edges=[(START, clarify)])
        outer_runner = InMemoryRunner(node=wf)
        session_id = str(uuid.uuid4())
        await outer_runner.session_service.create_session(
            app_name=outer_runner.app_name,
            user_id=outer_runner.app_name,
            session_id=session_id,
        )
        await _run_workflow_until_complete(outer_runner, session_id)

        session = await outer_runner.session_service.get_session(
            app_name=outer_runner.app_name,
            user_id=outer_runner.app_name,
            session_id=session_id,
        )
        result = session.state.get("clarification_result", {}) if session else {}
        return {
            "objectives": result.get("objectives", ""),
            "preferences": result.get("preferences", "no preference"),
            "context": result.get("context", "none"),
            "cancelled": result.get("cancelled", False),
        }

    return run_clarification_loop


def _accumulate_user_answer(ctx, resume: dict) -> None:
    answer = resume.get("result", "")
    history = ctx.state.get("qa_history", [])
    history.append({"q": ctx.state.get("pending_question", ""), "a": answer})
    ctx.state["qa_history"] = history


def _build_history_section(qa_history: list[dict]) -> str:
    if not qa_history:
        return ""
    lines = "\n".join(f"P: {item['q']}\nR: {item['a']}" for item in qa_history)
    return f"\n\nHistorial de preguntas y respuestas previas:\n{lines}"


async def _ask_clarifier_llm(model: object, prompt_with_history: str) -> ClarificationAction:
    inner = InMemoryRunner(
        agent=LlmAgent(
            name="clarifier_inner",
            model=model,
            instruction=prompt_with_history,
            output_schema=ClarificationAction,
            output_key="_action",
        ),
        app_name="clarifier_inner",
    )
    sid = str(uuid.uuid4())
    await inner.session_service.create_session(app_name="clarifier_inner", user_id="c", session_id=sid)
    async for _ in inner.run_async(
        user_id="c",
        session_id=sid,
        new_message=types.Content(role="user", parts=[types.Part(text="Procede.")]),
        run_config=RunConfig(max_llm_calls=_MAX_LLM_CALLS_PER_TURN),
    ):
        pass
    session = await inner.session_service.get_session(app_name="clarifier_inner", user_id="c", session_id=sid)
    raw = session.state.get("_action") if session else None
    if isinstance(raw, dict):
        return ClarificationAction.model_validate(raw)
    if isinstance(raw, ClarificationAction):
        return raw
    return ClarificationAction(action="cancel")


def _store_clarification_result(ctx, action: ClarificationAction) -> None:
    ctx.state["clarification_result"] = {
        "objectives": action.objectives,
        "preferences": action.preferences or "no preference",
        "context": action.context or "none",
        "cancelled": action.action == "cancel",
    }


def _extract_request_input(event) -> _RequestInputDetails | None:
    if not has_request_input_function_call(event):
        return None
    if not (event.content and event.content.parts):
        return None
    ids = get_request_input_interrupt_ids(event)
    if not ids:
        return None
    for part in event.content.parts:
        if part.function_call and part.function_call.args:
            args = part.function_call.args
            payload = args.get("payload") or {}
            return _RequestInputDetails(
                interrupt_id=ids[0],
                message=args.get("message", ""),
                options=payload.get("options", []),
                is_poll=payload.get("is_poll", False),
            )
    return None
