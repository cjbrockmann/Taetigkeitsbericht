from __future__ import annotations

from pydantic import BaseModel, Field


class Mandant(BaseModel):
    id: int = Field(ge=1, description="Primärschlüssel")
    mandant_name: str = Field(description="Mandantenname", max_length=80)
    mandant_kuerzel: str = Field(description="Mandantenkürzel", max_length=20)
