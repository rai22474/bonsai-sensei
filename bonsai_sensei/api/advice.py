import dataclasses
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from bonsai_sensei.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


class AdviceRequest(BaseModel):
    text: str
    user_id: str | None = "acceptance_user"


class ConfirmationAcceptRequest(BaseModel):
    user_id: str


@router.post("/advice")
async def get_advice(request_body: AdviceRequest, request: Request):
    logger.info(
        "*** Advice request received: user_id=%s text=%s ***",
        request_body.user_id,
        request_body.text,
    )

    advisor = getattr(request.app.state, "advisor", None)
    response = await advisor(request_body.text, user_id=request_body.user_id)

    return dataclasses.asdict(response)


@router.post("/advice/confirmations/{confirmation_id}/accept")
async def accept_confirmation(
    confirmation_id: str, request_body: ConfirmationAcceptRequest, request: Request
):
    confirmation_store = request.app.state.confirmation_store
    confirmation = confirmation_store.pop_pending_by_id(
        request_body.user_id, confirmation_id
    )
    if not confirmation:
        raise HTTPException(status_code=404, detail="confirmation_not_found")
    result = confirmation.execute()
    return {"status": "accepted", "result": result}
