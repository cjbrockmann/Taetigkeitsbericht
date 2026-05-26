from __future__ import annotations

from datetime import date
from typing import Optional

from ..interfaces.guthaben_urlaub_repository_interface import IGuthabenUrlaubRepository
from ..models.models_worktime import GuthabenUrlaub


class GuthabenUrlaubService:
    def __init__(self, repository: IGuthabenUrlaubRepository) -> None:
        self._repository = repository

    def erfasse_guthaben_urlaub(self, eintrag: GuthabenUrlaub) -> GuthabenUrlaub:
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
                f"Fuer Mandant {eintrag.mandant_id} existiert bereits ein GuthabenUrlaub-Eintrag "
                f"fuer {monat}."
            )
        return self._repository.save(eintrag)

    def hole_guthaben_urlaub(
        self, mandant_id: int, eintrag_id: int
    ) -> Optional[GuthabenUrlaub]:
        return self._repository.get_by_id(mandant_id, eintrag_id)

    def hole_guthaben_urlaub_fuer_monat(
        self, mandant_id: int, datum: date
    ) -> Optional[GuthabenUrlaub]:
        return self._repository.get_by_mandant_und_datum(mandant_id, datum)

    def liste_guthaben_urlaub(
        self, mandant_id: int, jahr: Optional[int] = None
    ) -> list[GuthabenUrlaub]:
        return self._repository.list_all(mandant_id, jahr=jahr)

    def loesche_guthaben_urlaub(self, mandant_id: int, eintrag_id: int) -> bool:
        return self._repository.delete_by_id(mandant_id, eintrag_id)
