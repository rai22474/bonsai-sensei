import json
import re
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

_PROPOSAL_INTERRUPT_ID = "plan-proposal-review"
_MAX_LLM_CALLS_PER_TURN = 10
_DRAFT_STATE_KEY = "plan_draft_in_progress"


class ProposalAction(BaseModel):
    action: Literal["propose", "cancel", "reclarify"]
    display_text: str = ""
    entries: list[dict] = []
    rationale: str = ""
    correction_prompt: str = "¿Qué cambios quieres hacer al plan?"


@dataclass
class _ProposalRequestDetails:
    interrupt_id: str
    display_text: str
    correction_prompt: str


def create_plan_proposal_runner(
    model: object, ask_human: Callable, ask_plan_review: Callable, app_name: str
) -> Callable:
    async def run_plan_proposal(rendered_prompt: str, outer_tool_context) -> dict:

        @node(rerun_on_resume=True)
        async def propose(ctx):
            resume = (ctx.resume_inputs or {}).get(_PROPOSAL_INTERRUPT_ID)
            if resume is not None:
                user_response = resume.get("result", "") if isinstance(resume, dict) else str(resume)
                if user_response == "confirmed":
                    _store_confirmed_proposal(ctx)
                    return
                if user_response == "cancelado":
                    ctx.state["proposal_result"] = {"cancelled": True, "reason": "usuario canceló"}
                    return
                _accumulate_correction(ctx, user_response)

            history = ctx.state.get("correction_history", [])
            prompt_with_history = rendered_prompt + _build_correction_history_section(history)
            action = await _ask_planner_llm(model, prompt_with_history)

            if action.action == "cancel":
                ctx.state["proposal_result"] = {"cancelled": True, "reason": "planner cancelled"}
                return

            if action.action == "reclarify":
                ctx.state["proposal_result"] = {"reclarify": True, "reason": action.rationale}
                return

            ctx.state["last_proposal"] = {"entries": action.entries, "rationale": action.rationale}
            outer_tool_context.state[_DRAFT_STATE_KEY] = action.display_text
            yield RequestInput(
                interrupt_id=_PROPOSAL_INTERRUPT_ID,
                message=action.display_text,
                payload={"correction_prompt": action.correction_prompt},
            )

        async def _review_proposal(ri: _ProposalRequestDetails) -> str:
            review_action = await ask_plan_review(ri.display_text, tool_context=outer_tool_context)
            if review_action == "confirmed":
                return "confirmed"
            if review_action == "correct":
                feedback = await ask_human(ri.correction_prompt, tool_context=outer_tool_context)
                return f"rechazado: {feedback}"
            return "cancelado"

        async def _run_workflow_until_complete(outer_runner, session_id) -> None:
            cur_msg = types.Content(role="user", parts=[types.Part(text="begin")])
            while True:
                request_details = None
                async for event in outer_runner.run_async(
                    user_id=outer_runner.app_name,
                    session_id=session_id,
                    new_message=cur_msg,
                ):
                    request_details = _extract_proposal_request(event) or request_details

                if request_details is None:
                    break

                user_response = await _review_proposal(request_details)
                outer_tool_context.state[_DRAFT_STATE_KEY] = None
                cur_msg = types.Content(
                    role="user",
                    parts=[create_request_input_response(request_details.interrupt_id, {"result": user_response})],
                )

        wf = Workflow(name=f"{app_name}_wf", edges=[(START, propose)])
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
        return session.state.get("proposal_result", {"cancelled": True, "reason": "max_llm_calls_reached"}) if session else {"cancelled": True, "reason": "session_lost"}

    return run_plan_proposal


def _accumulate_correction(ctx, user_response: str) -> None:
    feedback = user_response.removeprefix("rechazado: ")
    last = ctx.state.get("last_proposal", {})
    history = ctx.state.get("correction_history", [])
    history.append({"proposal_display": last.get("display_text", ""), "feedback": feedback})
    ctx.state["correction_history"] = history


def _store_confirmed_proposal(ctx) -> None:
    last = ctx.state.get("last_proposal", {})
    ctx.state["proposal_result"] = {
        "entries": last.get("entries", []),
        "rationale": last.get("rationale", ""),
    }


def _build_correction_history_section(correction_history: list[dict]) -> str:
    if not correction_history:
        return ""
    lines = [f"Corrección {i+1}: {item['feedback']}" for i, item in enumerate(correction_history)]
    return "\n\nHistorial de correcciones del usuario:\n" + "\n".join(lines)


async def _ask_planner_llm(model: object, prompt_with_history: str) -> ProposalAction:
    inner = InMemoryRunner(
        agent=LlmAgent(
            name="planner_inner",
            model=model,
            instruction=prompt_with_history,
        ),
        app_name="planner_inner",
    )
    sid = str(uuid.uuid4())
    await inner.session_service.create_session(app_name="planner_inner", user_id="p", session_id=sid)
    text_response = ""
    async for event in inner.run_async(
        user_id="p",
        session_id=sid,
        new_message=types.Content(role="user", parts=[types.Part(text="Genera el plan.")]),
        run_config=RunConfig(max_llm_calls=_MAX_LLM_CALLS_PER_TURN),
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    text_response = part.text
    return _parse_proposal_action(text_response)


def _parse_proposal_action(text: str) -> ProposalAction:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return ProposalAction(action="cancel")
    try:
        raw = json.loads(match.group())
        return ProposalAction.model_validate(raw)
    except (json.JSONDecodeError, Exception):
        return ProposalAction(action="cancel")


def _extract_proposal_request(event) -> _ProposalRequestDetails | None:
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
            return _ProposalRequestDetails(
                interrupt_id=ids[0],
                display_text=args.get("message", ""),
                correction_prompt=payload.get("correction_prompt", "¿Qué cambios quieres hacer al plan?"),
            )
    return None
