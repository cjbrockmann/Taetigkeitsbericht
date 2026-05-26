from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class Urlaubsantrag(BaseModel):
    id: Optional[int] = None
    datum_von: date = Field(description="Datum von")
    datum_bis: date = Field(description="Datum bis")
    urlaubstyp: str = Field(description="Urlaubstyp", max_length=80)
    urlaubstage: float = Field(description="Urlaubstage", ge=0)
    genehmigt: bool = Field(default=False, description="Genehmigt")

    @field_validator("urlaubstage")
    @classmethod
    def urlaubstage_nur_halbe_tage(cls, v: float) -> float:
        doppelt = v * 2
        if abs(doppelt - round(doppelt)) > 1e-6:
            raise ValueError(
                "Urlaubstage nur in Halbtags-Schritten (z. B. 1, 1.5, 2, 2.5)."
            )
        return v

    @model_validator(mode="after")
    def pruefe_datumsbereich(self) -> Urlaubsantrag:
        if self.datum_von > self.datum_bis:
            raise ValueError("datum_von muss vor oder gleich datum_bis liegen.")
        return self
