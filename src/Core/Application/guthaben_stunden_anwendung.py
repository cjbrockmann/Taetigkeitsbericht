from __future__ import annotations

from datetime import date
from typing import Optional

from Core.Domain.models.models_worktime import GuthabenStunden
from Core.Domain.services.guthaben_stunden_service import GuthabenStundenService


class GuthabenStundenAnwendung:
    def __init__(self, service: GuthabenStundenService) -> None:
        self._service = service

    def erfasse(self, eintrag: GuthabenStunden) -> GuthabenStunden:
        return self._service.erfasse_guthaben_stunden(eintrag)

    def hole(self, mandant_id: int, eintrag_id: int) -> Optional[GuthabenStunden]:
        return self._service.hole_guthaben_stunden(mandant_id, eintrag_id)

    def hole_fuer_monat(self, mandant_id: int, datum: date) -> Optional[GuthabenStunden]:
        return self._service.hole_guthaben_stunden_fuer_monat(mandant_id, datum)

    def liste(
        self, mandant_id: int, jahr: Optional[int] = None
    ) -> list[GuthabenStunden]:
        return self._service.liste_guthaben_stunden(mandant_id, jahr=jahr)

    def loesche(self, mandant_id: int, eintrag_id: int) -> bool:
        return self._service.loesche_guthaben_stunden(mandant_id, eintrag_id)
