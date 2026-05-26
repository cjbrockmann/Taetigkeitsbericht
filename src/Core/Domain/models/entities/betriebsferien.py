from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class Betriebsferien(BaseModel):
    id: Optional[int] = None
    mandant_id: Optional[int] = Field(default=None, description="Mandant ID")
    datum_von: date = Field(description="Datum von")
    datum_bis: date = Field(description="Datum bis")
    betriebsferienname: str = Field(description="Betriebsferienname", max_length=80)
    anmerkung: Optional[str] = Field(default=None, max_length=80)

    @model_validator(mode="after")
    def pruefe_datumsbereich(self) -> Betriebsferien:
        if self.datum_von > self.datum_bis:
            raise ValueError("datum_von muss vor oder gleich datum_bis liegen.")
        return self
