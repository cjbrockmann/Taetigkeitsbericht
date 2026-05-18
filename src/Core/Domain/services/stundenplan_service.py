from __future__ import annotations

from datetime import time

from ..models.models_worktime import Stundenplan
from ..interfaces.stundenplan_repository_interface import IStundenplanRepository


class StundenplanService:
    def __init__(self, repository: IStundenplanRepository) -> None:
        self._repository = repository

    def erfasse_stundenplaneintrag(self, eintrag: Stundenplan) -> Stundenplan:
        if eintrag.mandant_id is None:
            raise ValueError("mandant_id ist erforderlich.")
        vorhandene_eintraege = self._repository.get_by_wochentag(
            eintrag.mandant_id, eintrag.wochentag
        )
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
                    "Der Zeitraum ueberschneidet sich mit einem bestehenden Stundenplaneintrag am selben Wochentag."
                )
        return self._repository.save(eintrag)

    def hole_stundenplan(self, mandant_id: int, wochentag: int) -> list[Stundenplan]:
        return self._repository.get_by_wochentag(mandant_id, wochentag)

    def liste_stundenplan_eintraege(self, mandant_id: int) -> list[Stundenplan]:
        return self._repository.list_all(mandant_id)

    def loesche_stundenplan(self, mandant_id: int, wochentag: int) -> bool:
        return self._repository.delete_by_wochentag(mandant_id, wochentag)

    def loesche_stundenplan_per_id(self, mandant_id: int, eintrag_id: int) -> bool:
        return self._repository.delete_by_id(mandant_id, eintrag_id)

    @staticmethod
    def _zeitraeume_ueberschneiden_sich(
        neuer_von: time,
        neuer_bis: time,
        bestehender_von: time,
        bestehender_bis: time,
    ) -> bool:
        return neuer_von < bestehender_bis and bestehender_von < neuer_bis
