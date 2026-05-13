from __future__ import annotations

from typing import Optional

from Core.Domain.models.models_worktime import Schulferien
from Core.Domain.services.schulferien_service import SchulferienService


class SchulferienAnwendung:
    def __init__(self, service: SchulferienService) -> None:
        self._service = service

    def erfasse(self, eintrag: Schulferien) -> Schulferien:
        return self._service.erfasse_schulferien(eintrag)

    def hole(self, eintrag_id: int) -> Optional[Schulferien]:
        return self._service.hole_schulferien(eintrag_id)

    def liste(self, jahr: Optional[int] = None) -> list[Schulferien]:
        return self._service.liste_schulferien(jahr=jahr)

    def loesche(self, eintrag_id: int) -> bool:
        return self._service.loesche_schulferien(eintrag_id)

    def importiere_aus_api(self, jahr: int) -> tuple[int, int, int]:
        return self._service.importiere_schulferien_aus_api(jahr)
