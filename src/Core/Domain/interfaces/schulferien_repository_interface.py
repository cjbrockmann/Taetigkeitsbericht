from __future__ import annotations

from typing import Optional, Protocol

from ..models.models_worktime import Schulferien


class ISchulferienRepository(Protocol):
    def save(self, eintrag: Schulferien) -> Schulferien:
        ...

    def get_by_id(self, eintrag_id: int) -> Optional[Schulferien]:
        ...

    def list_all(self, jahr: Optional[int] = None) -> list[Schulferien]:
        ...

    def delete_by_id(self, eintrag_id: int) -> bool:
        ...
