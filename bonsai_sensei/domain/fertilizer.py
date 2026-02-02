from typing import Optional
from sqlmodel import Field, SQLModel
from sqlalchemy import Column, JSON


class Fertilizer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    usage_sheet: str = Field(default="")
    recommended_amount: str = Field(default="")
    sources: list[str] = Field(default_factory=list, sa_column=Column(JSON))