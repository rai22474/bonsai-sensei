from typing import Optional
from sqlmodel import Field, SQLModel, Relationship
from bonsai_sensei.domain.species import Species


class Bonsai(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    species_id: int = Field(foreign_key="species.id")
    wiki_path: Optional[str] = Field(default=None)
    user_id: Optional[str] = Field(default=None, foreign_key="user_settings.user_id", index=True)
    species: Species | None = Relationship(back_populates="bonsais")
