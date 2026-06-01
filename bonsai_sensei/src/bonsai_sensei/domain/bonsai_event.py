from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class BonsaiEvent(SQLModel, table=True):
    __tablename__ = "bonsai_event"

    id: Optional[int] = Field(default=None, primary_key=True)
    bonsai_id: int = Field(
        sa_column=Column(Integer, ForeignKey("bonsai.id", ondelete="CASCADE"), index=True, nullable=False)
    )
    event_type: str = Field(index=True)
    payload: Dict[str, Any] = Field(default={}, sa_column=Column(JSONB))
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
