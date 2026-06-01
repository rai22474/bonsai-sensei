from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from bonsai_sensei.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()

class MessageRequest(BaseModel):
    chat_id: str
    text: str

@router.post("/send")
async def send_message(request_body: MessageRequest, request: Request):
    logger.info(f"Attempting to send message to {request_body.chat_id}")
    
    bot = getattr(request.app.state, "bot", None)
    if not bot:
         logger.error("Bot instance not found in app state")
         raise HTTPException(status_code=500, detail="Bot not initialized")

    await bot.send_message(chat_id=request_body.chat_id, text=request_body.text)
    return {"status": "success", "message": "Message sent"}
