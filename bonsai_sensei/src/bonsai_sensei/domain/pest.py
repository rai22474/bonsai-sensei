from typing import Optional
from sqlmodel import Field, SQLModel


class Pest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    wiki_path: Optional[str] = Field(default=None)
