from datetime import date, datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import Column, ForeignKey, Integer, JSON
from sqlmodel import Field, SQLModel


class PlannedWorkPhoto(SQLModel, table=True):
    __tablename__ = "planned_work_photo"

    planned_work_id: int = Field(
        sa_column=Column(Integer, ForeignKey("plannedwork.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    )
    photo_id: int = Field(
        sa_column=Column(Integer, ForeignKey("bonsai_photo.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    )


class PlannedWork(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    bonsai_id: int = Field(foreign_key="bonsai.id", ondelete="CASCADE")
    plan_id: Optional[int] = Field(default=None, foreign_key="fertilizationplan.id", ondelete="SET NULL")
    phytosanitary_plan_id: Optional[int] = Field(default=None, foreign_key="phytosanitaryplan.id", ondelete="SET NULL")
    development_plan_id: Optional[int] = Field(default=None, foreign_key="developmentplan.id", ondelete="SET NULL")
    work_type: str = Field(index=True)
    payload: Dict[str, Any] = Field(sa_column=Column(JSON))
    scheduled_date: date
    notes: Optional[str] = Field(default=None)
    refinement_wiki_path: Optional[str] = Field(default=None)
    result_wiki_path: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
