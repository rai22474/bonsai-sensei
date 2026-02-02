from typing import Optional
from sqlmodel import Field, SQLModel


class Phytosanitary(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    usage_sheet: str = Field(default="")
    recommended_amount: str = Field(default="")
    recommended_for: str = Field(default="")