from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from bonsai_sensei.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


class AdviceRequest(BaseModel):
    text: str
    user_id: str | None = "acceptance_user"


@router.post("/advice")
async def get_advice(request_body: AdviceRequest, request: Request):
    logger.info(
        "*** Advice request received: user_id=%s text=%s ***",
        request_body.user_id,
        request_body.text,
    )
    advisor = getattr(request.app.state, "advisor", None)
    if not advisor:
        logger.error("Advisor not initialized")
        raise HTTPException(status_code=500, detail="Advisor not initialized")
    response = await advisor(request_body.text, user_id=request_body.user_id)
    logger.info(
        "*** Advice response generated: user_id=%s ***",
        request_body.user_id,
    )
    return {"response": response}
