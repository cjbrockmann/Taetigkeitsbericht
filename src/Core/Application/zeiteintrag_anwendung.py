from __future__ import annotations

from datetime import date
from typing import Optional
from uuid import UUID

from Core.Domain.models.models_worktime import Stundenplan, Zeiteintrag
from Core.Domain.services.zeiteintrag_service import ZeiteintragService
from Core.Domain.services.stundenplan_service import StundenplanService


class ZeiteintragAnwendung:
    def __init__(self, service: ZeiteintragService) -> None:
        self._service = service

    def erfasse(self, eintrag: Zeiteintrag) -> Zeiteintrag:
        return self._service.erfasse_zeiteintrag(eintrag)

    def erfasse_aus_stundenplan(
        self, mandant_id: int, datum: date, stundenplan_eintrag: Stundenplan
    ) -> Zeiteintrag:
        # Wie Stundenplan.wochentag: 1 = Montag, 7 = Sonntag (ISO 8601)
        erwarteter_wochentag = datum.isoweekday()
        if stundenplan_eintrag.wochentag != erwarteter_wochentag:
            raise ValueError(
                "Das Datum passt nicht zum Wochentag des Stundenplaneintrags "
                f"(Stundenplan: {stundenplan_eintrag.wochentag}, "
                f"fuer das Datum erwartet: {erwarteter_wochentag})."
            )
        zeiteintrag = Zeiteintrag(
            mandant_id=mandant_id,
            datum=datum,
            uhrzeit_von=stundenplan_eintrag.uhrzeit_von,
            uhrzeit_bis=stundenplan_eintrag.uhrzeit_bis,
            pause_beginn=stundenplan_eintrag.pause_beginn,
            pause_ende=stundenplan_eintrag.pause_ende,
            pause2_beginn=stundenplan_eintrag.pause2_beginn,
            pause2_ende=stundenplan_eintrag.pause2_ende,
            anmerkung=stundenplan_eintrag.anmerkung,
        )
        return self.erfasse(zeiteintrag)

    def hole_fuer_datum(self, mandant_id: int, datum: date) -> list[Zeiteintrag]:
        return self._service.hole_zeiteintrag(mandant_id, datum)

    def liste(
        self,
        mandant_id: int,
        jahr: Optional[int] = None,
        monat: Optional[int] = None,
    ) -> list[Zeiteintrag]:
        return self._service.liste_zeiteintraege(mandant_id, jahr=jahr, monat=monat)

    def loesche_fuer_datum(self, mandant_id: int, datum: date) -> bool:
        return self._service.loesche_zeiteintrag(mandant_id, datum)

    def loesche_per_id(self, mandant_id: int, eintrag_id: UUID) -> bool:
        return self._service.loesche_zeiteintrag_per_id(mandant_id, eintrag_id)
