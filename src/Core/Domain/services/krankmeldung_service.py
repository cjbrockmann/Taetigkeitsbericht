from __future__ import annotations

from typing import Optional

from ..interfaces.krankmeldung_repository_interface import IKrankmeldungRepository
from ..models.models_worktime import Krankmeldung


class KrankmeldungService:
    def __init__(self, repository: IKrankmeldungRepository) -> None:
        self._repository = repository

    def erfasse_krankmeldung(self, eintrag: Krankmeldung) -> Krankmeldung:
        for vorhanden in self._repository.list_all(jahr=None):
            if eintrag.id is not None and vorhanden.id == eintrag.id:
                continue
            if (
                eintrag.krank_von <= vorhanden.krank_bis
                and vorhanden.krank_von <= eintrag.krank_bis
            ):
                von_s = vorhanden.krank_von.strftime("%d.%m.%Y")
                bis_s = vorhanden.krank_bis.strftime("%d.%m.%Y")
                raise ValueError(
                    f"Zeitraum ueberlappt mit vorhandener Krankmeldung ({von_s} bis {bis_s})."
                )
        return self._repository.save(eintrag)

    def hole_krankmeldung(self, eintrag_id: int) -> Optional[Krankmeldung]:
        return self._repository.get_by_id(eintrag_id)

    def liste_krankmeldungen(self, jahr: Optional[int] = None) -> list[Krankmeldung]:
        return self._repository.list_all(jahr=jahr)

    def loesche_krankmeldung(self, eintrag_id: int) -> bool:
        return self._repository.delete_by_id(eintrag_id)
