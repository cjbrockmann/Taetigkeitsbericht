from __future__ import annotations

from typing import Optional

from ..interfaces.betriebsferien_repository_interface import IBetriebsferienRepository
from ..models.models_worktime import Betriebsferien


class BetriebsferienService:
    def __init__(self, repository: IBetriebsferienRepository) -> None:
        self._repository = repository

    def erfasse_betriebsferien(self, eintrag: Betriebsferien) -> Betriebsferien:
        for vorhanden in self._repository.list_all(jahr=None):
            if eintrag.id is not None and vorhanden.id == eintrag.id:
                continue
            if (
                eintrag.datum_von <= vorhanden.datum_bis
                and vorhanden.datum_von <= eintrag.datum_bis
            ):
                von_s = vorhanden.datum_von.strftime("%d.%m.%Y")
                bis_s = vorhanden.datum_bis.strftime("%d.%m.%Y")
                raise ValueError(
                    f"Zeitraum ueberlappt mit vorhandenen Betriebsferien ({von_s} bis {bis_s})."
                )
        return self._repository.save(eintrag)

    def hole_betriebsferien(self, eintrag_id: int) -> Optional[Betriebsferien]:
        return self._repository.get_by_id(eintrag_id)

    def liste_betriebsferien(self, jahr: Optional[int] = None) -> list[Betriebsferien]:
        return self._repository.list_all(jahr=jahr)

    def loesche_betriebsferien(self, eintrag_id: int) -> bool:
        return self._repository.delete_by_id(eintrag_id)
