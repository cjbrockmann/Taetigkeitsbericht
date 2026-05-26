from __future__ import annotations

from datetime import date
from typing import Optional
from uuid import UUID

from pydantic import Field

from .arbeitszeit_basis import ArbeitszeitBasis


class Zeiteintrag(ArbeitszeitBasis):
    id: Optional[UUID] = None
    mandant_id: Optional[int] = Field(default=None, description="Mandant ID")
    datum: date
