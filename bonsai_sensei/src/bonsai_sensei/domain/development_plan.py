from datetime import date, datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class DevelopmentPlan(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    bonsai_id: int = Field(foreign_key="bonsai.id", ondelete="CASCADE")
    development_path: str
    current_phase: str
    target_style: str
    design_goal: str
    period_start: date
    period_end: date
    status: str = Field(default="active")
    wiki_path: str
    abandonment_reason: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    abandoned_at: Optional[datetime] = Field(default=None)
