from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class GuthabenStunden(BaseModel):
    id: Optional[int] = Field(default=None, description="Primärschlüssel")
    mandant_id: Optional[int] = Field(default=None, description="Mandant ID")
    datum: date = Field(description="Datum")
    stunden_guthaben_vormonat: float = Field(
        default=0,
        description="Saldo Vormonat: positiv = Guthaben, negativ = Defizit",
    )
    stunden_guthaben_vormonat_manuell: Optional[float] = Field(
        default=None,
        description="Nur manuelle Korrektur (Formular), wird nicht berechnet",
    )
    stunden_guthaben_monatsende_aktuell: float = Field(
        default=0,
        description="Saldo Monatsende: positiv = Guthaben, negativ = Defizit",
    )

    @model_validator(mode="after")
    def pruefe_datum(self) -> GuthabenStunden:
        if self.datum.day != 1:
            raise ValueError("Datum muss der 1. eines Monats sein.")
        return self
