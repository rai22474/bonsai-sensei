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

    task = asyncio.create_task(advisor(request_body.text, user_id=user_id))
    active_tasks[user_id] = task

    while not task.done():
        await asyncio.sleep(0.05)
        pending = pending_human_responses.get(user_id)
        if pending and pending.get("type") == "confirmation":
            return {
                "text": "",
                "pending_confirmations": [
                    {"id": pending["confirmation_id"], "summary": pending.get("summary", "")}
                ],
            }
        if pending and pending.get("type") == "selection":
            return {
                "text": "",
                "pending_selections": [
                    {
                        "id": pending["selection_id"],
                        "question": pending.get("question", ""),
                        "options": pending.get("options", []),
                    }
                ],
            }

    active_tasks.pop(user_id, None)
    if task.exception():
        raise task.exception()
    return dataclasses.asdict(task.result())


@router.delete("/advice/sessions/{user_id}", status_code=204)
async def reset_session(user_id: str, request: Request):
    await request.app.state.reset_session(user_id)


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
        task = active_tasks.get(user_id)
        if task:
            try:
                await asyncio.wait_for(asyncio.shield(task), timeout=30)
                active_tasks.pop(user_id, None)
            except asyncio.TimeoutError:
                pass
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


class SelectionChooseRequest(BaseModel):
    user_id: str
    option: str


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
            while not task.done():
                await asyncio.sleep(0.05)
                next_pending = pending_human_responses.get(user_id)
                if next_pending is not None and next_pending.get("selection_id") != selection_id:
                    if next_pending.get("type") == "confirmation":
                        return {
                            "status": "chosen",
                            "option": request_body.option,
                            "pending_confirmations": [
                                {"id": next_pending["confirmation_id"], "summary": next_pending.get("summary", "")}
                            ],
                        }
                    if next_pending.get("type") == "selection":
                        return {
                            "status": "chosen",
                            "option": request_body.option,
                            "pending_selections": [
                                {
                                    "id": next_pending["selection_id"],
                                    "question": next_pending.get("question", ""),
                                    "options": next_pending.get("options", []),
                                }
                            ],
                        }
            active_tasks.pop(user_id, None)
            if task.exception():
                raise task.exception()
        return {"status": "chosen", "option": request_body.option}

    raise HTTPException(status_code=404, detail="selection_not_found")


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

    while not task.done():
        await asyncio.sleep(0.05)
        pending = pending_human_responses.get(user_id)
        if pending and pending.get("type") == "confirmation":
            return {
                "text": "",
                "pending_confirmations": [
                    {"id": pending["confirmation_id"], "summary": pending.get("summary", "")}
                ],
            }
        if pending and pending.get("type") == "selection":
            return {
                "text": "",
                "pending_selections": [
                    {
                        "id": pending["selection_id"],
                        "question": pending.get("question", ""),
                        "options": pending.get("options", []),
                    }
                ],
            }

    active_tasks.pop(user_id, None)
    if task.exception():
        raise task.exception()
    return dataclasses.asdict(task.result())
