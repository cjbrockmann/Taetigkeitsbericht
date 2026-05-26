from __future__ import annotations

from datetime import date
from typing import Optional, Protocol

from ..models.models_worktime import GuthabenUrlaub


class IGuthabenUrlaubRepository(Protocol):
    def save(self, eintrag: GuthabenUrlaub) -> GuthabenUrlaub:
        ...

    def get_by_id(self, mandant_id: int, eintrag_id: int) -> Optional[GuthabenUrlaub]:
        ...

    def get_by_mandant_und_datum(
        self, mandant_id: int, datum: date
    ) -> Optional[GuthabenUrlaub]:
        ...

    def list_all(self, mandant_id: int, jahr: Optional[int] = None) -> list[GuthabenUrlaub]:
        ...

    def delete_by_id(self, mandant_id: int, eintrag_id: int) -> bool:
        ...
