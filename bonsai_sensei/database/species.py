from typing import Optional, Dict
from sqlmodel import Field, SQLModel
from sqlalchemy import Column, JSON


class Species(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    scientific_name: Optional[str] = Field(default=None, index=True)
    care_guide: Dict = Field(default={}, sa_column=Column(JSON))
