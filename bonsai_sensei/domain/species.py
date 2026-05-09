from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:
    from bonsai_sensei.domain.bonsai import Bonsai


class SpeciesCategory(str, Enum):
    conifer = "conifer"
    deciduous = "deciduous"
    flowering = "flowering"
    tropical = "tropical"
    broadleaf = "broadleaf"
    fruiting = "fruiting"
    unknown = "unknown"


CATEGORY_EMOJI: dict[SpeciesCategory, str] = {
    SpeciesCategory.conifer: "🌲",
    SpeciesCategory.deciduous: "🍂",
    SpeciesCategory.flowering: "🌸",
    SpeciesCategory.tropical: "🌿",
    SpeciesCategory.broadleaf: "🌳",
    SpeciesCategory.fruiting: "🍊",
    SpeciesCategory.unknown: "🌱",
}


class Species(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    scientific_name: Optional[str] = Field(default=None, index=True)
    wiki_path: Optional[str] = Field(default=None)
    category: SpeciesCategory = Field(default=SpeciesCategory.unknown)
    bonsais: List["Bonsai"] = Relationship(back_populates="species")

    def get_emoji(self) -> str:
        return CATEGORY_EMOJI.get(self.category, "🌱")
