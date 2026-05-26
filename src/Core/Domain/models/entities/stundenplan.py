from __future__ import annotations

from typing import Optional

from pydantic import Field

from .arbeitszeit_basis import ArbeitszeitBasis


class Stundenplan(ArbeitszeitBasis):
    id: Optional[int] = None
    mandant_id: Optional[int] = Field(default=None, description="Mandant ID")
    wochentag: int = Field(ge=1, le=7, description="1=Montag, 7=Sonntag")
