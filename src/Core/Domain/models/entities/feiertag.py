from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class Feiertag(BaseModel):
    datum: date
    feiertagsname: str = Field(max_length=80, description="Name des Feiertags")
    hinweis: Optional[str] = Field(
        default=None, max_length=80, description="Zusatzinfo, z. B. aus Feiertags-API"
    )
    ist_halber_tag: bool = Field(
        default=False, description="True = halber Feiertag, False = ganzer Feiertag"
    )
    ist_offiziell: bool = Field(
        default=True, description="True = gesetzlicher/offizieller Feiertag"
    )
