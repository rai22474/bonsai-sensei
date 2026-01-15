from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from bonsai_sensei.telegram.bot import bot
from bonsai_sensei.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()

class MessageRequest(BaseModel):
    chat_id: str
    text: str

@router.post("/send")
async def send_message(request: MessageRequest):
    logger.info(f"Attempting to send message to {request.chat_id}")
    
    await bot.send_message(chat_id=request.chat_id, text=request.text)
    return {"status": "success", "message": "Message sent"}
