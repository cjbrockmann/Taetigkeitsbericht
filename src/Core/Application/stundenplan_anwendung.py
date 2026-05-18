from __future__ import annotations

from Core.Domain.models.models_worktime import Stundenplan
from Core.Domain.services.stundenplan_service import StundenplanService


class StundenplanAnwendung:
    def __init__(self, service: StundenplanService) -> None:
        self._service = service

    def erfasse(self, eintrag: Stundenplan) -> Stundenplan:
        return self._service.erfasse_stundenplaneintrag(eintrag)

    def hole_fuer_wochentag(self, mandant_id: int, wochentag: int) -> list[Stundenplan]:
        return self._service.hole_stundenplan(mandant_id, wochentag)

    def liste(self, mandant_id: int) -> list[Stundenplan]:
        return self._service.liste_stundenplan_eintraege(mandant_id)

    def loesche_fuer_wochentag(self, mandant_id: int, wochentag: int) -> bool:
        return self._service.loesche_stundenplan(mandant_id, wochentag)

    def loesche_per_id(self, mandant_id: int, eintrag_id: int) -> bool:
        return self._service.loesche_stundenplan_per_id(mandant_id, eintrag_id)
