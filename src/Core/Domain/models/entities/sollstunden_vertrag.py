from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class SollstundenVertrag(BaseModel):
    id: Optional[int] = Field(default=None, description="Primärschlüssel")
    mandant_id: Optional[int] = Field(default=None, description="Mandant ID")
    effective_date: date = Field(description="Datum, ab dem die Regel gelten soll")
    discontinued_date: Optional[date] = Field(
        default=None, description="Datum, ab dem die Regel nicht mehr gelten soll"
    )
    Montag: float = Field(ge=0, description="Montag", default=0)
    Dienstag: float = Field(ge=0, description="Dienstag", default=0)
    Mittwoch: float = Field(ge=0, description="Mittwoch", default=0)
    Donnerstag: float = Field(ge=0, description="Donnerstag", default=0)
    Freitag: float = Field(ge=0, description="Freitag", default=0)
    Samstag: float = Field(ge=0, description="Samstag", default=0)
    Sonntag: float = Field(ge=0, description="Sonntag", default=0)

    @model_validator(mode="after")
    def pruefe_discontinued_date(self) -> SollstundenVertrag:
        if self.discontinued_date and self.discontinued_date <= self.effective_date:
            raise ValueError("discontinued_date muss nach effective_date liegen.")
        return self
