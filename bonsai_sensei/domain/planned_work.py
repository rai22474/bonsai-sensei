from datetime import date, datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


class PlannedWork(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    bonsai_id: int = Field(foreign_key="bonsai.id", ondelete="CASCADE")
    work_type: str = Field(index=True)
    payload: Dict[str, Any] = Field(sa_column=Column(JSON))
    scheduled_date: date
    notes: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
