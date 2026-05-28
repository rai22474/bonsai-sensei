import asyncio
import dataclasses
import io

from fastapi import APIRouter, HTTPException, Request, UploadFile, Form
from google.genai import types
from PIL import Image
from pydantic import BaseModel

from bonsai_sensei.domain.services.human_input import ConfirmationResult
from bonsai_sensei.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


class AdviceRequest(BaseModel):
    text: str
    user_id: str | None = "acceptance_user"


class ConfirmationAcceptRequest(BaseModel):
    user_id: str


class ConfirmationRejectRequest(BaseModel):
    user_id: str
    reason: str = ""


class TextResponseRequest(BaseModel):
    user_id: str
    text: str


class SelectionChooseRequest(BaseModel):
    user_id: str
    option: str


class PlanReviewConfirmRequest(BaseModel):
    user_id: str


def _build_pending_interrupt(pending: dict) -> dict:
    """Maps a pending human input state to its API interrupt fields."""
    pending_type = pending.get("type")
    if pending_type == "confirmation":
        return {"pending_confirmations": [{"id": pending["confirmation_id"], "summary": pending.get("summary", "")}]}
    if pending_type == "selection":
        return {"pending_selections": [{"id": pending["selection_id"], "question": pending.get("question", ""), "options": pending.get("options", [])}]}
    if pending_type in ("text", "poll"):
        return {"pending_text_questions": [{"question": pending.get("question", pending.get("summary", ""))}]}
    if pending_type == "plan_review":
        return {"pending_plan_reviews": [{"id": pending["review_id"]}]}
    return {}


async def _wait_for_next_pending(
    task,
    user_id: str,
    pending_human_responses: dict,
    prior_pending=None,
    deadline: float | None = None,
) -> dict | None:
    """Poll until task completes, a new interrupt appears, or deadline is reached.

    Returns the interrupt dict if a new pending state appears, None if the task completed or deadline was reached.
    When prior_pending is None, any pending state triggers an interrupt.
    """
    loop = asyncio.get_event_loop()
    while not task.done():
        await asyncio.sleep(0.05)
        if deadline is not None and loop.time() > deadline:
            return None
        current = pending_human_responses.get(user_id)
        if current is not None and (prior_pending is None or current is not prior_pending):
            return _build_pending_interrupt(current)
    return None


def _pop_completed_task(task, active_tasks: dict, user_id: str):
    active_tasks.pop(user_id, None)
    if task.exception():
        raise task.exception()
    return dataclasses.asdict(task.result())


@router.post("/advice")
async def get_advice(request_body: AdviceRequest, request: Request):
    logger.info(
        "*** Advice request received: user_id=%s text=%s ***",
        request_body.user_id,
        request_body.text,
    )
    user_id = request_body.user_id
    advisor = request.app.state.advisor
    pending_human_responses = getattr(request.app.state, "pending_human_responses", {})
    active_tasks = getattr(request.app.state, "active_tasks", {})

    existing_task = active_tasks.get(user_id)
    if existing_task and not existing_task.done():
        existing_task.cancel()
        try:
            await existing_task
        except (asyncio.CancelledError, Exception):
            pass
    pending_human_responses.pop(user_id, None)

    task = asyncio.create_task(advisor(request_body.text, user_id=user_id))
    active_tasks[user_id] = task

    interrupt = await _wait_for_next_pending(task, user_id, pending_human_responses)
    if interrupt:
        return {"text": "", **interrupt}
    return _pop_completed_task(task, active_tasks, user_id)


@router.delete("/advice/sessions/{user_id}", status_code=204)
async def reset_session(user_id: str, request: Request):
    active_tasks = getattr(request.app.state, "active_tasks", {})
    task = active_tasks.pop(user_id, None)
    if task and not task.done():
        task.cancel()
        try:
            await task
        except (asyncio.CancelledError, Exception):
            pass
    pending_human_responses = getattr(request.app.state, "pending_human_responses", {})
    pending_human_responses.pop(user_id, None)
    await request.app.state.reset_session(user_id)
    mem0_client = getattr(request.app.state, "mem0_client", None)
    if mem0_client is not None:
        await mem0_client.delete_all(user_id=user_id)


@router.post("/advice/confirmations/{confirmation_id}/accept")
async def accept_confirmation(
    confirmation_id: str, request_body: ConfirmationAcceptRequest, request: Request
):
    user_id = request_body.user_id
    pending_human_responses = getattr(request.app.state, "pending_human_responses", {})
    active_tasks = getattr(request.app.state, "active_tasks", {})

    pending = pending_human_responses.get(user_id)
    if pending and pending.get("confirmation_id") == confirmation_id:
        pending["response"] = ConfirmationResult(accepted=True)
        pending["event"].set()
        loop = asyncio.get_event_loop()
        consume_deadline = loop.time() + 10
        while pending_human_responses.get(user_id) is pending:
            if loop.time() > consume_deadline:
                break
            await asyncio.sleep(0.05)
        task = active_tasks.get(user_id)
        if task:
            interrupt = await _wait_for_next_pending(
                task, user_id, pending_human_responses, prior_pending=pending, deadline=loop.time() + 120
            )
            if not task.done():
                return {"status": "accepted", **(interrupt or {})}
            active_tasks.pop(user_id, None)
            if task.exception():
                raise task.exception()
        return {"status": "accepted"}

    raise HTTPException(status_code=404, detail="confirmation_not_found")


@router.post("/advice/confirmations/{confirmation_id}/reject")
async def reject_confirmation(
    confirmation_id: str, request_body: ConfirmationRejectRequest, request: Request
):
    user_id = request_body.user_id
    pending_human_responses = getattr(request.app.state, "pending_human_responses", {})
    active_tasks = getattr(request.app.state, "active_tasks", {})

    pending = pending_human_responses.get(user_id)
    if pending and pending.get("confirmation_id") == confirmation_id:
        pending["response"] = ConfirmationResult(accepted=False, reason=request_body.reason)
        pending["event"].set()
        task = active_tasks.get(user_id)
        if task:
            try:
                await asyncio.wait_for(asyncio.shield(task), timeout=30)
                active_tasks.pop(user_id, None)
            except asyncio.TimeoutError:
                pass
        return {"status": "rejected"}

    raise HTTPException(status_code=404, detail="confirmation_not_found")


@router.post("/advice/text-response")
async def submit_text_response(request_body: TextResponseRequest, request: Request):
    user_id = request_body.user_id
    pending_human_responses = getattr(request.app.state, "pending_human_responses", {})
    active_tasks = getattr(request.app.state, "active_tasks", {})

    pending = pending_human_responses.get(user_id)
    if pending and pending.get("type") in ("text", "poll"):
        pending["response"] = request_body.text
        pending["event"].set()
        task = active_tasks.get(user_id)
        if task:
            interrupt = await _wait_for_next_pending(task, user_id, pending_human_responses, prior_pending=pending)
            if interrupt:
                return {"text": "", **interrupt}
            return _pop_completed_task(task, active_tasks, user_id)
        return {"text": ""}

    raise HTTPException(status_code=404, detail="text_question_not_found")


@router.post("/advice/selections/{selection_id}/choose")
async def choose_selection(
    selection_id: str, request_body: SelectionChooseRequest, request: Request
):
    user_id = request_body.user_id
    pending_human_responses = getattr(request.app.state, "pending_human_responses", {})
    active_tasks = getattr(request.app.state, "active_tasks", {})

    pending = pending_human_responses.get(user_id)
    if pending and pending.get("selection_id") == selection_id:
        pending["response"] = request_body.option
        pending["event"].set()
        task = active_tasks.get(user_id)
        if task:
            loop = asyncio.get_event_loop()
            interrupt = await _wait_for_next_pending(
                task, user_id, pending_human_responses, prior_pending=pending, deadline=loop.time() + 8
            )
            if not task.done():
                return {"status": "chosen", "option": request_body.option, **(interrupt or {})}
            active_tasks.pop(user_id, None)
            if task.exception():
                raise task.exception()
        return {"status": "chosen", "option": request_body.option}

    raise HTTPException(status_code=404, detail="selection_not_found")


@router.post("/advice/plan-reviews/{review_id}/confirm")
async def confirm_plan_review(
    review_id: str, request_body: PlanReviewConfirmRequest, request: Request
):
    user_id = request_body.user_id
    pending_human_responses = getattr(request.app.state, "pending_human_responses", {})
    active_tasks = getattr(request.app.state, "active_tasks", {})

    pending = pending_human_responses.get(user_id)
    if pending and pending.get("review_id") == review_id:
        pending["response"] = "confirmed"
        pending["event"].set()
        task = active_tasks.get(user_id)
        if task:
            try:
                await asyncio.wait_for(asyncio.shield(task), timeout=30)
                active_tasks.pop(user_id, None)
            except asyncio.TimeoutError:
                pass
        return {"status": "confirmed"}

    raise HTTPException(status_code=404, detail="plan_review_not_found")


@router.post("/advice/photos")
async def upload_photo(
    photo: UploadFile,
    user_id: str = Form(default="acceptance_user"),
    request: Request = None,
):
    raw_bytes = await photo.read()
    webp_buffer = io.BytesIO()
    Image.open(io.BytesIO(raw_bytes)).save(webp_buffer, format="WEBP", quality=85)
    webp_bytes = webp_buffer.getvalue()

    pending_photos = getattr(request.app.state, "pending_photos", {})
    pending_photos[user_id] = webp_bytes

    advisor = request.app.state.advisor
    pending_human_responses = getattr(request.app.state, "pending_human_responses", {})
    active_tasks = getattr(request.app.state, "active_tasks", {})

    message = types.Content(
        role="user",
        parts=[
            types.Part(inline_data=types.Blob(mime_type="image/webp", data=webp_bytes)),
            types.Part(text="El usuario ha enviado una foto."),
        ],
    )

    task = asyncio.create_task(advisor(message, user_id=user_id))
    active_tasks[user_id] = task

    interrupt = await _wait_for_next_pending(task, user_id, pending_human_responses)
    if interrupt:
        return {"text": "", **interrupt}
    return _pop_completed_task(task, active_tasks, user_id)
