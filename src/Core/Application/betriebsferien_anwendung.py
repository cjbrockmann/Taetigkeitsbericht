from __future__ import annotations

from typing import Optional

from Core.Domain.models.models_worktime import Betriebsferien
from Core.Domain.services.betriebsferien_service import BetriebsferienService


class BetriebsferienAnwendung:
    def __init__(self, service: BetriebsferienService) -> None:
        self._service = service

    def erfasse(self, eintrag: Betriebsferien) -> Betriebsferien:
        return self._service.erfasse_betriebsferien(eintrag)

    def hole(self, mandant_id: int, eintrag_id: int) -> Optional[Betriebsferien]:
        return self._service.hole_betriebsferien(mandant_id, eintrag_id)

    def liste(self, mandant_id: int, jahr: Optional[int] = None) -> list[Betriebsferien]:
        return self._service.liste_betriebsferien(mandant_id, jahr=jahr)

    def loesche(self, mandant_id: int, eintrag_id: int) -> bool:
        return self._service.loesche_betriebsferien(mandant_id, eintrag_id)
