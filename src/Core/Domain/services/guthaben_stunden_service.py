from __future__ import annotations

from datetime import date
from typing import Optional

from ..interfaces.guthaben_stunden_repository_interface import IGuthabenStundenRepository
from ..models.models_worktime import GuthabenStunden


class GuthabenStundenService:
    def __init__(self, repository: IGuthabenStundenRepository) -> None:
        self._repository = repository

    def erfasse_guthaben_stunden(self, eintrag: GuthabenStunden) -> GuthabenStunden:
        if eintrag.mandant_id is None:
            raise ValueError("mandant_id ist erforderlich.")
        vorhanden = self._repository.get_by_mandant_und_datum(
            eintrag.mandant_id, eintrag.datum
        )
        if vorhanden is not None and (
            eintrag.id is None or vorhanden.id != eintrag.id
        ):
            monat = eintrag.datum.strftime("%m.%Y")
            raise ValueError(
                f"Fuer Mandant {eintrag.mandant_id} existiert bereits ein Stundenguthaben "
                f"fuer {monat}."
            )
        return self._repository.save(eintrag)

    def hole_guthaben_stunden(
        self, mandant_id: int, eintrag_id: int
    ) -> Optional[GuthabenStunden]:
        return self._repository.get_by_id(mandant_id, eintrag_id)

    def hole_guthaben_stunden_fuer_monat(
        self, mandant_id: int, datum: date
    ) -> Optional[GuthabenStunden]:
        return self._repository.get_by_mandant_und_datum(mandant_id, datum)

    def liste_guthaben_stunden(
        self, mandant_id: int, jahr: Optional[int] = None
    ) -> list[GuthabenStunden]:
        return self._repository.list_all(mandant_id, jahr=jahr)

    def loesche_guthaben_stunden(self, mandant_id: int, eintrag_id: int) -> bool:
        return self._repository.delete_by_id(mandant_id, eintrag_id)
