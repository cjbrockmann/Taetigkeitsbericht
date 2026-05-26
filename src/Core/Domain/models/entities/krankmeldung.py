from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class Krankmeldung(BaseModel):
    id: Optional[int] = None
    krank_von: date = Field(description="Krank von")
    krank_bis: date = Field(description="Krank bis")
    krankmeldungstage: int = Field(description="Krankmeldungstage", ge=0)
    anmerkung: Optional[str] = Field(default=None, max_length=80)

    @model_validator(mode="after")
    def pruefe_datumsbereich(self) -> Krankmeldung:
        if self.krank_von > self.krank_bis:
            raise ValueError("krank_von muss vor oder gleich krank_bis liegen.")
        return self
