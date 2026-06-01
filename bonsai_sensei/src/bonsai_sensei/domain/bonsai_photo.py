from datetime import date, datetime, timezone
from typing import Optional
from sqlalchemy import Column, ForeignKey, Integer
from sqlmodel import Field, SQLModel


class BonsaiPhoto(SQLModel, table=True):
    __tablename__ = "bonsai_photo"

    id: Optional[int] = Field(default=None, primary_key=True)
    bonsai_id: int = Field(
        sa_column=Column(Integer, ForeignKey("bonsai.id", ondelete="CASCADE"), index=True, nullable=False)
    )
    file_path: str
    taken_on: date = Field(default_factory=lambda: datetime.now(timezone.utc).date())
