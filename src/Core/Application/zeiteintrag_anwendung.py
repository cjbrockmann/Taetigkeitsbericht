from __future__ import annotations

import json
from calendar import monthrange
from datetime import date, time
from typing import Optional
from uuid import UUID

from Core.Domain.models.models_worktime import (
    Betriebsferien,
    Feiertag,
    Krankmeldung,
    Schulferien,
    Stundenplan,
    Urlaubsantrag,
    Zeiteintrag,
    ZeiteintragsDTO,
)
from Core.Domain.services.zeiteintrag_service import ZeiteintragService
from Core.Domain.services.stundenplan_service import StundenplanService
from Core.Domain.services.feiertag_service import FeiertagService 
from Core.Domain.services.urlaubsantrag_service import UrlaubsantragService
from Core.Domain.services.krankmeldung_service import KrankmeldungService
from Core.Domain.services.schulferien_service import SchulferienService
from Core.Domain.services.betriebsferien_service import BetriebsferienService


class ZeiteintragAnwendung:
    def __init__(self, service: ZeiteintragService) -> None:
        self._service = service

    def erfasse(self, eintrag: Zeiteintrag) -> Zeiteintrag:
        return self._service.erfasse_zeiteintrag(eintrag)

    def erfasse_aus_stundenplan(
        self, datum: date, stundenplan_eintrag: Stundenplan
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

    def hole_fuer_datum(self, datum: date) -> list[Zeiteintrag]:
        return self._service.hole_zeiteintrag(datum)

    def liste(self, jahr: Optional[int] = None, monat: Optional[int] = None) -> list[Zeiteintrag]:
        return self._service.liste_zeiteintraege(jahr=jahr, monat=monat)

    def loesche_fuer_datum(self, datum: date) -> bool:
        return self._service.loesche_zeiteintrag(datum)

    def loesche_per_id(self, eintrag_id: UUID) -> bool:
        return self._service.loesche_zeiteintrag_per_id(eintrag_id)


class ZeiteintragAnwendungDTO(ZeiteintragAnwendung):
    
    def __init__(self, serviceZeiteintrag: ZeiteintragService, 
               serviceStundenplan: StundenplanService, 
               serviceFeiertage: FeiertagService, 
               serviceUrlaub: UrlaubsantragService,
               serviceKrank: KrankmeldungService,
               serviceSchulferien: SchulferienService,
               serviceBetriebsferien: BetriebsferienService,
               ) -> None:
        super().__init__(serviceZeiteintrag)
        self._serviceStundenplan = serviceStundenplan
        self._serviceFeiertage = serviceFeiertage
        self._serviceUrlaub = serviceUrlaub
        self._serviceKrank = serviceKrank
        self._serviceSchulferien = serviceSchulferien
        self._serviceBetriebsferien = serviceBetriebsferien
        self.stundenplan_eintraege: list[Stundenplan] = []
        self.feiertage: list[Feiertag] = []
        self.urlaubsantraege: list[Urlaubsantrag] = []
        self.krankmeldungen: list[Krankmeldung] = []
        self.schulferien: list[Schulferien] = []
        self.betriebsferien: list[Betriebsferien] = []
        self._geladenes_jahr: Optional[int] = None

    # ----------------------------------------------------------------------  
    #   Overwrite der Basisfunktionen

    def erfasse(self, eintrag: ZeiteintragsDTO) -> ZeiteintragsDTO:
        parent_erfasse = super().erfasse(self._dto_zu_zeiteintrag(eintrag))
        return self._zeiteintrag_zu_dto(parent_erfasse)	

    def erfasse_aus_stundenplan(
        self, datum: date, stundenplan_eintrag: Stundenplan
    ) -> ZeiteintragsDTO:
        parent_erfasse_aus_stundenplan = super().erfasse_aus_stundenplan(datum, stundenplan_eintrag)
        return self._zeiteintrag_zu_dto(parent_erfasse_aus_stundenplan)

    def hole_fuer_datum(self, datum: date) -> list[ZeiteintragsDTO]:
        parent_hole_fuer_datum = super().hole_fuer_datum(datum)
        return list(map(self._zeiteintrag_zu_dto, parent_hole_fuer_datum))

    def liste(self, jahr: Optional[int] = None, monat: Optional[int] = None) -> list[ZeiteintragsDTO]:
        parent_liste = super().liste(jahr=jahr, monat=monat)
        result = list(map(self._zeiteintrag_zu_dto, parent_liste))
        return result

    def liste_im_monat(self, jahr: int, monat: int) -> list[ZeiteintragsDTO]:

        self._initialisiere_jahresdaten(jahr, force=True)  # Sicherstellen, dass alle Daten für das Jahr geladen sind
        parent_liste = super().liste(jahr=jahr, monat=monat)
        eintraege = list(map(self._zeiteintrag_zu_dto, parent_liste))

        eintraege_nach_tag: dict[date, list[ZeiteintragsDTO]] = {}
        for eintrag in eintraege:
            eintraege_nach_tag.setdefault(eintrag.datum, []).append(eintrag)

        tage_im_monat = monthrange(jahr, monat)[1]
        alle_eintraege: list[ZeiteintragsDTO] = []
        for tag in range(1, tage_im_monat + 1):
            aktuelles_datum = date(jahr, monat, tag)
            tages_eintraege = eintraege_nach_tag.get(aktuelles_datum, [])
            if tages_eintraege:
                alle_eintraege.extend(tages_eintraege)
            else:
                alle_eintraege.append(ZeiteintragsDTO(
                    id=None,
                    datum=aktuelles_datum,
                    uhrzeit_von=None,
                    uhrzeit_bis=None,
                ))

        for eintrag in alle_eintraege:
            self._initialisiere_dto(eintrag)        

        return alle_eintraege

    def loesche_fuer_datum(self, datum: date) -> bool:
        return super().loesche_fuer_datum(datum)
    
    def loesche_per_id(self, eintrag_id: UUID) -> bool:
        return super().loesche_per_id(eintrag_id)

    # ----------------------------------------------------------------------  
    #   Hilfsfunktionen
    def _initialisiere_jahresdaten(self, jahr: int, force: bool = False) -> None:
        if self._geladenes_jahr == jahr and not force:     
            return  # Bereits geladen, nichts zu tun
        self._geladenes_jahr = jahr

        if not self.stundenplan_eintraege or force:
            self.stundenplan_eintraege = self._serviceStundenplan.liste_stundenplan_eintraege()

        if not any(e.datum.year == jahr for e in self.feiertage) or force:
            self.feiertage = self._serviceFeiertage.liste_feiertage(jahr)

        if not any(e.datum_von.year == jahr or e.datum_bis.year == jahr for e in self.urlaubsantraege) or force:
            self.urlaubsantraege = self._serviceUrlaub.liste_urlaubsantraege(jahr)

        if not any(e.krank_von.year == jahr or e.krank_bis.year == jahr for e in self.krankmeldungen) or force:
            self.krankmeldungen = self._serviceKrank.liste_krankmeldungen(jahr)

        if not any(e.datum_von.year == jahr or e.datum_bis.year == jahr for e in self.schulferien) or force:
            self.schulferien = self._serviceSchulferien.liste_schulferien(jahr)

        if not any(e.datum_von.year == jahr or e.datum_bis.year == jahr for e in self.betriebsferien) or force:
            self.betriebsferien = self._serviceBetriebsferien.liste_betriebsferien(jahr)


    def _sekunden_seit_mitternacht(self, t: time) -> int:
        return t.hour * 3600 + t.minute * 60 + t.second

    def _netto_arbeitssekunden(self, eintrag: Zeiteintrag) -> int:
        von_s = self._sekunden_seit_mitternacht(eintrag.uhrzeit_von)
        bis_s = self._sekunden_seit_mitternacht(eintrag.uhrzeit_bis)
        brutto = bis_s - von_s
        for pause_a, pause_b in (
            (eintrag.pause_beginn, eintrag.pause_ende),
            (eintrag.pause2_beginn, eintrag.pause2_ende),
        ):
            if pause_a is not None and pause_b is not None:
                pa = max(von_s, self._sekunden_seit_mitternacht(pause_a))
                pb = min(bis_s, self._sekunden_seit_mitternacht(pause_b))
                if pb > pa:
                    brutto -= pb - pa
        return max(0, brutto)

    def _sekunden_als_uhrzeit_fuer_dauer(self, sekunden: int) -> time:
        """Darstellung einer Dauer als datetime.time (hh:mm:ss, max. 23:59:59)."""
        sekunden = max(0, sekunden)
        if sekunden >= 24 * 3600:
            return time(23, 59, 59)
        h = sekunden // 3600
        m, s = divmod(sekunden % 3600, 60)
        return time(hour=h, minute=m, second=s)

    def _berechne_soll_stunden_nach_stundenplan(self, datum: date) -> time | None:
        """Berechnet die Soll-Arbeitszeit anhand des Stundenplans für den Wochentag des Datums."""
        wochentag = datum.isoweekday()  # 1=Montag, 7=Sonntag (ISO 8601)
        stundenplan_eintrag = next(
            (e for e in self.stundenplan_eintraege if e.wochentag == wochentag),
            None
        )
        if stundenplan_eintrag is None:
            return None
        netto_s = self._netto_arbeitssekunden(stundenplan_eintrag)
        return self._sekunden_als_uhrzeit_fuer_dauer(netto_s)

    def _initialisiere_dto(self, eintrag: ZeiteintragsDTO) -> ZeiteintragsDTO:
        eintrag.ist_urlaub = any(obj.datum_von <= eintrag.datum <= obj.datum_bis for obj in self.urlaubsantraege)
        eintrag.ist_krank = any(obj.krank_von <= eintrag.datum <= obj.krank_bis for obj in self.krankmeldungen)
        eintrag.ist_feiertag = any(obj.datum == eintrag.datum for obj in self.feiertage)
        eintrag.ist_ferien = any(obj.datum_von <= eintrag.datum <= obj.datum_bis for obj in self.schulferien)
        eintrag.ist_betriebsferien = any(
            obj.datum_von <= eintrag.datum <= obj.datum_bis for obj in self.betriebsferien
        )
        eintrag.feiertagsname = next((f.feiertagsname for f in self.feiertage if f.datum == eintrag.datum), None)
        eintrag.schulferienname = next((s.schulferienname for s in self.schulferien if s.datum_von <= eintrag.datum <= s.datum_bis), None)

        if eintrag.uhrzeit_von is not None and eintrag.uhrzeit_bis is not None:
            eintrag.geleistete_stunden = self._sekunden_als_uhrzeit_fuer_dauer(
                self._netto_arbeitssekunden(eintrag)
            )
            eintrag.soll_stunden_nach_Stundenplan = self._berechne_soll_stunden_nach_stundenplan(eintrag.datum)

        return eintrag

    def _leerer_eintrag_dto(self, datum: date) -> ZeiteintragsDTO:
        return self._initialisiere_dto(ZeiteintragsDTO(
            id=None,
            datum=datum,
            uhrzeit_von=None,
            uhrzeit_bis=None,
            pause_beginn = None,
            pause_ende   = None,
            pause2_beginn= None,
            pause2_ende  = None,
            anmerkung    = None,            
        ))    


    def _zeiteintrag_zu_dto(self, eintrag: Zeiteintrag) -> ZeiteintragsDTO:
        jahr = eintrag.datum.year
        self._initialisiere_jahresdaten(jahr)
        netto_s = self._netto_arbeitssekunden(eintrag)
        dto = self._initialisiere_dto(ZeiteintragsDTO(
            id=eintrag.id,
            datum=eintrag.datum,
            uhrzeit_von  = eintrag.uhrzeit_von,
            uhrzeit_bis  = eintrag.uhrzeit_bis,
            pause_beginn = eintrag.pause_beginn,
            pause_ende   = eintrag.pause_ende,
            pause2_beginn= eintrag.pause2_beginn,
            pause2_ende  = eintrag.pause2_ende,
            anmerkung    = eintrag.anmerkung,
        ))
        return dto

    def _dto_zu_zeiteintrag(self, eintrag: ZeiteintragsDTO) -> Zeiteintrag:
        if eintrag.uhrzeit_von is None or eintrag.uhrzeit_bis is None:
            return None
        return Zeiteintrag(
            id=eintrag.id,
            datum=eintrag.datum,
            uhrzeit_von=time(0, 0, 0) if eintrag.uhrzeit_von is None else eintrag.uhrzeit_von,
            uhrzeit_bis=time(0, 0, 1) if eintrag.uhrzeit_bis is None else eintrag.uhrzeit_bis,
            pause_beginn=eintrag.pause_beginn,
            pause_ende=eintrag.pause_ende,
            pause2_beginn=eintrag.pause2_beginn,
            pause2_ende=eintrag.pause2_ende,
            anmerkung=eintrag.anmerkung,
        )



