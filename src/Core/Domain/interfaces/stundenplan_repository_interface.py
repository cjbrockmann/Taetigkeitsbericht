from __future__ import annotations

from typing import Protocol

from ..models.models_worktime import Stundenplan


class IStundenplanRepository(Protocol):
    def save(self, eintrag: Stundenplan) -> Stundenplan:
        ...

    def get_by_wochentag(self, mandant_id: int, wochentag: int) -> list[Stundenplan]:
        ...

    def list_all(self, mandant_id: int) -> list[Stundenplan]:
        ...

    def delete_by_wochentag(self, mandant_id: int, wochentag: int) -> bool:
        ...

    def delete_by_id(self, mandant_id: int, eintrag_id: int) -> bool:
        ...
