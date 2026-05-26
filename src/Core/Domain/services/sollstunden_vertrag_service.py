from __future__ import annotations

from datetime import date
from typing import Optional

from ..interfaces.sollstunden_vertrag_repository_interface import ISollstundenVertragRepository
from ..models.models_worktime import SollstundenVertrag


def _zeitraeume_ueberlappen(a: SollstundenVertrag, b: SollstundenVertrag) -> bool:
    """Ueberlappung von [effective_date, discontinued_date) — discontinued_date exklusiv."""
    ende_a = a.discontinued_date or date.max
    ende_b = b.discontinued_date or date.max
    return a.effective_date < ende_b and b.effective_date < ende_a


class SollstundenVertragService:
    def __init__(self, repository: ISollstundenVertragRepository) -> None:
        self._repository = repository

    def erfasse_sollstunden_vertrag(self, vertrag: SollstundenVertrag) -> SollstundenVertrag:
        if vertrag.mandant_id is None:
            raise ValueError("mandant_id ist erforderlich.")
        for vorhanden in self._repository.list_all(vertrag.mandant_id):
            if vertrag.id is not None and vorhanden.id == vertrag.id:
                continue
            if _zeitraeume_ueberlappen(vertrag, vorhanden):
                von_s = vorhanden.effective_date.strftime("%d.%m.%Y")
                bis_s = (
                    vorhanden.discontinued_date.strftime("%d.%m.%Y")
                    if vorhanden.discontinued_date
                    else "offen"
                )
                raise ValueError(
                    "Der Gueltigkeitszeitraum ueberlappt mit einem bestehenden Vertrag "
                    f"({von_s} bis {bis_s})."
                )
        return self._repository.save(vertrag)

    def hole_sollstunden_vertrag(
        self, mandant_id: int, vertrag_id: int
    ) -> Optional[SollstundenVertrag]:
        return self._repository.get_by_id(mandant_id, vertrag_id)

    def hole_gueltigen_vertrag_fuer_datum(
        self, mandant_id: int, datum: date
    ) -> Optional[SollstundenVertrag]:
        return self._repository.get_gueltig_fuer_datum(mandant_id, datum)

    def liste_sollstunden_vertraege(self, mandant_id: int) -> list[SollstundenVertrag]:
        return self._repository.list_all(mandant_id)

    def loesche_sollstunden_vertrag(self, mandant_id: int, vertrag_id: int) -> bool:
        return self._repository.delete_by_id(mandant_id, vertrag_id)

    def hat_eintraege(self) -> bool:
        return self._repository.hat_eintraege()
