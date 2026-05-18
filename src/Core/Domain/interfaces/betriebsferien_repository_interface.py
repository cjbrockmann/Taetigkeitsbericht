from __future__ import annotations

from typing import Optional, Protocol

from ..models.models_worktime import Betriebsferien


class IBetriebsferienRepository(Protocol):
    def save(self, eintrag: Betriebsferien) -> Betriebsferien:
        ...

    def get_by_id(self, mandant_id: int, eintrag_id: int) -> Optional[Betriebsferien]:
        ...

    def list_all(self, mandant_id: int, jahr: Optional[int] = None) -> list[Betriebsferien]:
        ...

    def delete_by_id(self, mandant_id: int, eintrag_id: int) -> bool:
        ...
