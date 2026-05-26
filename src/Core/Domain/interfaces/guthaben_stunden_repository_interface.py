from __future__ import annotations

from datetime import date
from typing import Optional, Protocol

from ..models.models_worktime import GuthabenStunden


class IGuthabenStundenRepository(Protocol):
    def save(self, eintrag: GuthabenStunden) -> GuthabenStunden:
        ...

    def get_by_id(self, mandant_id: int, eintrag_id: int) -> Optional[GuthabenStunden]:
        ...

    def get_by_mandant_und_datum(
        self, mandant_id: int, datum: date
    ) -> Optional[GuthabenStunden]:
        ...

    def list_all(self, mandant_id: int, jahr: Optional[int] = None) -> list[GuthabenStunden]:
        ...

    def delete_by_id(self, mandant_id: int, eintrag_id: int) -> bool:
        ...
