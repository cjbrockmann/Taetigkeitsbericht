from __future__ import annotations

from datetime import date
from typing import Optional, Protocol

from ..models.models_worktime import SollstundenVertrag


class ISollstundenVertragRepository(Protocol):
    def save(self, vertrag: SollstundenVertrag) -> SollstundenVertrag:
        ...

    def get_by_id(self, mandant_id: int, vertrag_id: int) -> Optional[SollstundenVertrag]:
        ...

    def list_all(self, mandant_id: int) -> list[SollstundenVertrag]:
        ...

    def get_gueltig_fuer_datum(
        self, mandant_id: int, datum: date
    ) -> Optional[SollstundenVertrag]:
        ...

    def delete_by_id(self, mandant_id: int, vertrag_id: int) -> bool:
        ...

    def hat_eintraege(self) -> bool:
        ...
