from __future__ import annotations

from datetime import date
from typing import Optional, Protocol
from uuid import UUID

from ..models.models_worktime import Zeiteintrag


class IZeiteintragRepository(Protocol):
    def save(self, eintrag: Zeiteintrag) -> Zeiteintrag:
        ...

    def get_by_datum(self, mandant_id: int, datum: date) -> list[Zeiteintrag]:
        ...

    def list_all(
        self,
        mandant_id: int,
        jahr: Optional[int] = None,
        monat: Optional[int] = None,
    ) -> list[Zeiteintrag]:
        ...

    def delete_by_datum(self, mandant_id: int, datum: date) -> bool:
        ...

    def delete_by_id(self, mandant_id: int, eintrag_id: UUID) -> bool:
        ...
