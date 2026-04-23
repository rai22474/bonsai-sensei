import asyncio
import dataclasses

from fastapi import APIRouter, HTTPException, Request
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
