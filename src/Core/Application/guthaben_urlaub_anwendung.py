from __future__ import annotations

from datetime import date
from typing import Optional

from Core.Domain.models.models_worktime import GuthabenUrlaub
from Core.Domain.services.guthaben_urlaub_service import GuthabenUrlaubService


class GuthabenUrlaubAnwendung:
    def __init__(self, service: GuthabenUrlaubService) -> None:
        self._service = service

    def erfasse(self, eintrag: GuthabenUrlaub) -> GuthabenUrlaub:
        return self._service.erfasse_guthaben_urlaub(eintrag)

    def hole(self, mandant_id: int, eintrag_id: int) -> Optional[GuthabenUrlaub]:
        return self._service.hole_guthaben_urlaub(mandant_id, eintrag_id)

    def hole_fuer_monat(self, mandant_id: int, datum: date) -> Optional[GuthabenUrlaub]:
        return self._service.hole_guthaben_urlaub_fuer_monat(mandant_id, datum)

    def liste(
        self, mandant_id: int, jahr: Optional[int] = None
    ) -> list[GuthabenUrlaub]:
        return self._service.liste_guthaben_urlaub(mandant_id, jahr=jahr)

    def loesche(self, mandant_id: int, eintrag_id: int) -> bool:
        return self._service.loesche_guthaben_urlaub(mandant_id, eintrag_id)
