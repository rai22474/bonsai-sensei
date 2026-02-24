from typing import Optional
from sqlmodel import Field, SQLModel


class UserSettings(SQLModel, table=True):
    __tablename__ = "user_settings"
    user_id: str = Field(primary_key=True)
    location: Optional[str] = Field(default=None)
    telegram_chat_id: Optional[str] = Field(default=None)
