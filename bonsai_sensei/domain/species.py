from typing import Optional, List, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:
    from bonsai_sensei.domain.bonsai import Bonsai


class Species(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    scientific_name: Optional[str] = Field(default=None, index=True)
    wiki_path: Optional[str] = Field(default=None)
    bonsais: List["Bonsai"] = Relationship(back_populates="species")
