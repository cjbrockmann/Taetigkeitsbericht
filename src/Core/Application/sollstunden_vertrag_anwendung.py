from __future__ import annotations

from datetime import date
from typing import Optional

from Core.Domain.models.models_worktime import SollstundenVertrag
from Core.Domain.services.sollstunden_vertrag_service import SollstundenVertragService


class SollstundenVertragAnwendung:
    def __init__(self, service: SollstundenVertragService) -> None:
        self._service = service

    def erfasse(self, vertrag: SollstundenVertrag) -> SollstundenVertrag:
        return self._service.erfasse_sollstunden_vertrag(vertrag)

    def hole(self, mandant_id: int, vertrag_id: int) -> Optional[SollstundenVertrag]:
        return self._service.hole_sollstunden_vertrag(mandant_id, vertrag_id)

    def hole_gueltig_fuer_datum(
        self, mandant_id: int, datum: date
    ) -> Optional[SollstundenVertrag]:
        return self._service.hole_gueltigen_vertrag_fuer_datum(mandant_id, datum)

    def liste(self, mandant_id: int) -> list[SollstundenVertrag]:
        return self._service.liste_sollstunden_vertraege(mandant_id)

    def loesche(self, mandant_id: int, vertrag_id: int) -> bool:
        return self._service.loesche_sollstunden_vertrag(mandant_id, vertrag_id)

    def hat_eintraege(self) -> bool:
        """True, wenn die Tabelle sollstunden_vertrag mindestens einen Datensatz hat."""
        return self._service.hat_eintraege()
