from __future__ import annotations

from calendar import monthrange
from datetime import date, time
from typing import Optional
from uuid import UUID

from ..models.models_worktime import Zeiteintrag
from ..interfaces.zeiteintrag_repository_interface import IZeiteintragRepository


class ZeiteintragService:
    def __init__(self, repository: IZeiteintragRepository) -> None:
        self._repository = repository

    def erfasse_zeiteintrag(self, eintrag: Zeiteintrag) -> Zeiteintrag:
        if eintrag.mandant_id is None:
            raise ValueError("mandant_id ist erforderlich.")
        vorhandene_eintraege = self._repository.get_by_datum(eintrag.mandant_id, eintrag.datum)
        for vorhandener_eintrag in vorhandene_eintraege:
            if eintrag.id is not None and vorhandener_eintrag.id == eintrag.id:
                continue
            if self._zeitraeume_ueberschneiden_sich(
                eintrag.uhrzeit_von,
                eintrag.uhrzeit_bis,
                vorhandener_eintrag.uhrzeit_von,
                vorhandener_eintrag.uhrzeit_bis,
            ):
                raise ValueError(
                    "Der Zeitraum ueberschneidet sich mit einem bestehenden Zeiteintrag am selben Datum."
                )
        return self._repository.save(eintrag)

    def hole_zeiteintrag(self, mandant_id: int, datum: date) -> list[Zeiteintrag]:
        return self._repository.get_by_datum(mandant_id, datum)

    def liste_zeiteintraege(
        self,
        mandant_id: int,
        jahr: Optional[int] = None,
        monat: Optional[int] = None,
    ) -> list[Zeiteintrag]:
        return self._repository.list_all(mandant_id, jahr=jahr, monat=monat)

    def loesche_zeiteintrag(self, mandant_id: int, datum: date) -> bool:
        return self._repository.delete_by_datum(mandant_id, datum)

    def loesche_zeiteintrag_per_id(self, mandant_id: int, eintrag_id: UUID) -> bool:
        return self._repository.delete_by_id(mandant_id, eintrag_id)

    @staticmethod
    def _get_monatstage(jahr: int, monat: int) -> list[date]:
        _, anzahl_tage = monthrange(jahr, monat)
        return [date(jahr, monat, tag) for tag in range(1, anzahl_tage + 1)]

    @staticmethod
    def _zeitraeume_ueberschneiden_sich(
        neuer_von: time,
        neuer_bis: time,
        bestehender_von: time,
        bestehender_bis: time,
    ) -> bool:
        return neuer_von < bestehender_bis and bestehender_von < neuer_bis
