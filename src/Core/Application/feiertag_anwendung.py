from __future__ import annotations

from datetime import date
from typing import Optional

from Core.Domain.services.feiertag_service import FeiertagService
from Core.Domain.models.models_worktime import Feiertag


class FeiertagAnwendung:
    def __init__(self, service: FeiertagService) -> None:
        self._service = service

    def erfasse(self, eintrag: Feiertag) -> Feiertag:
        return self._service.erfasse_feiertag(eintrag)

    def aktualisiere(self, eintrag: Feiertag) -> bool:
        return self._service.aktualisiere_feiertag(eintrag)

    def hole_fuer_datum(self, datum: date) -> list[Feiertag]:
        return self._service.hole_feiertag(datum)

    def liste(self, jahr: Optional[int] = None) -> list[Feiertag]:
        return self._service.liste_feiertage(jahr=jahr)

    def loesche_fuer_datum(self, datum: date) -> bool:
        return self._service.loesche_feiertag(datum)

    def lade_aus_api(self, jahr: int) -> tuple[int, int]:
        return self._service.importiere_feiertage_aus_api(jahr=jahr)
