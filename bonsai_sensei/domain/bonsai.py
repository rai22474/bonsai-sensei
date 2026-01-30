from typing import Optional
from sqlmodel import Field, SQLModel, Relationship
from bonsai_sensei.domain.species import Species


class Bonsai(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    species_id: int = Field(foreign_key="species.id")
    species: Species | None = Relationship(back_populates="bonsais")
