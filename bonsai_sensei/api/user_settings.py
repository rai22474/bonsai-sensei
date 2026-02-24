from fastapi import APIRouter, Request
from pydantic import BaseModel
from bonsai_sensei.domain.user_settings import UserSettings

router = APIRouter()


class UserSettingsRequest(BaseModel):
    location: str | None = None
    telegram_chat_id: str | None = None


@router.put("/users/{user_id}/settings")
async def save_user_settings(user_id: str, request_body: UserSettingsRequest, request: Request):
    
    user_settings = UserSettings(
        user_id=user_id,
        location=request_body.location,
        telegram_chat_id=request_body.telegram_chat_id,
    )
    saved = request.app.state.user_settings_service["save_user_settings"](user_settings)
    return {"user_id": saved.user_id, "location": saved.location, "telegram_chat_id": saved.telegram_chat_id}


@router.get("/users/{user_id}/settings")
async def get_user_settings(user_id: str, request: Request):
    user_settings = request.app.state.user_settings_service["get_user_settings"](user_id)
    if not user_settings:
        return None
    return {"user_id": user_settings.user_id, "location": user_settings.location, "telegram_chat_id": user_settings.telegram_chat_id}


@router.delete("/users/{user_id}/settings")
async def delete_user_settings(user_id: str, request: Request):
    deleted = request.app.state.user_settings_service["delete_user_settings"](user_id)
    return {"deleted": deleted}
