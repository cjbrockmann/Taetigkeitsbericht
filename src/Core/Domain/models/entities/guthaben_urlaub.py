from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class GuthabenUrlaub(BaseModel):
    id: Optional[int] = Field(default=None, description="Primärschlüssel")
    mandant_id: Optional[int] = Field(default=None, description="Mandant ID")
    datum: date = Field(description="Datum")
    urlaubstage_guthaben_vorjahr: float = Field(
        ge=0, description="Guthaben des Vormonats", default=0
    )
    urlaubstage_guthaben_vormonat: float = Field(
        ge=0, description="Guthaben des Vormonats", default=0
    )
    urlaubstage_im_monat_aktuell: float = Field(
        ge=0, description="Urlaub im aktuellen Monat verbraucht", default=0
    )
    guthaben_vormonat_korrektur: Optional[float] = Field(
        ge=0, description="Guthaben des aktuellen Monats", default=0
    )


    @model_validator(mode="after")
    def pruefe_datum(self) -> GuthabenUrlaub:
        if self.datum.day != 1:
            raise ValueError("Datum muss der 1. eines Monats sein.")
        return self
