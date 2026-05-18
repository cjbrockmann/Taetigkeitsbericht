from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime, time
from typing import Optional
from uuid import UUID

from Core.Application.zeiteintrag_anwendung import ZeiteintragAnwendung
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
from Core.Domain.services.betriebsferien_service import BetriebsferienService
from Core.Domain.services.feiertag_service import FeiertagService
from Core.Domain.services.krankmeldung_service import KrankmeldungService
from Core.Domain.services.schulferien_service import SchulferienService
from Core.Domain.services.stundenplan_service import StundenplanService
from Core.Domain.services.urlaubsantrag_service import UrlaubsantragService
from Core.Domain.services.zeiteintrag_service import ZeiteintragService


class ZeiteintragAnwendungDTO(ZeiteintragAnwendung):
    _MAX_ANMERKUNG_LAENGE = 80

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
        self._vertrag_stunden_nach_wochentag: dict[int, str] = {}
        self._sollstunden_an_feiertagen: bool = False
        self._kommentar_urlaubstage: str = ""
        self._kommentar_krankheitstage: str = ""
        self._kommentar_ueberstunden_frei: str = "Überstunden frei"

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

    def liste_im_monat(
        self,
        jahr: int,
        monat: int,
        *,
        stundenplan_eintraege: list[Stundenplan] | None = None,
    ) -> list[ZeiteintragsDTO]:

        if stundenplan_eintraege is not None:
            self.stundenplan_eintraege = list(stundenplan_eintraege)
        self._initialisiere_jahresdaten(jahr, force=True)
        parent_liste = super().liste(jahr=jahr, monat=monat)
        eintraege = [self._basiseintrag_aus_zeiteintrag(e) for e in parent_liste]

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
                alle_eintraege.append(
                    ZeiteintragsDTO(
                        id=None,
                        datum=aktuelles_datum,
                        uhrzeit_von=None,
                        uhrzeit_bis=None,
                    )
                )

        eintraege_nach_tag.clear()
        for eintrag in alle_eintraege:
            self._initialisiere_dto(eintrag)
            eintraege_nach_tag.setdefault(eintrag.datum, []).append(eintrag)

        for eintraege_fuer_tag in eintraege_nach_tag.values():
            self.anreichere_eintraege_fuer_tag(eintraege_fuer_tag)

        return alle_eintraege

    def anreichere_eintraege_fuer_tag(self, eintraege: list[ZeiteintragsDTO]) -> None:
        """Flags, Kommentarregeln und Soll-Felder fuer alle Zeilen eines Kalendertags."""
        if not eintraege:
            return
        jahr = eintraege[0].datum.year
        self._initialisiere_jahresdaten(jahr)
        for eintrag in eintraege:
            self._initialisiere_dto(eintrag)
            self._wende_kommentar_regeln_an(eintrag)
        self._setze_soll_felder_fuer_tag(eintraege)
        self._aktualisiere_geleistete_stunden_fuer_tag(eintraege)

    def loesche_fuer_datum(self, datum: date) -> bool:
        return super().loesche_fuer_datum(datum)
    
    def loesche_per_id(self, eintrag_id: UUID) -> bool:
        return super().loesche_per_id(eintrag_id)

    # ----------------------------------------------------------------------  
    #   Hilfsfunktionen
    def set_stundenplan_eintraege(self, eintraege: list[Stundenplan]) -> None:
        """Setzt den Stundenplan-Cache (z. B. aus der aktuellen Stundenplan-Tabelle)."""
        self.stundenplan_eintraege = list(eintraege)

    def _initialisiere_jahresdaten(self, jahr: int, force: bool = False) -> None:
        if self._geladenes_jahr == jahr and not force:     
            return  # Bereits geladen, nichts zu tun
        self._geladenes_jahr = jahr

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

    def _stundenplan_bloecke_fuer_datum(self, datum: date) -> list[Stundenplan]:
        """Stundenplan-Eintraege des Wochentags, sortiert nach Beginn (wie in der GUI)."""
        wochentag = datum.isoweekday()
        return sorted(
            (e for e in self.stundenplan_eintraege if e.wochentag == wochentag),
            key=lambda e: self._sekunden_seit_mitternacht(e.uhrzeit_von),
        )

    def _verteile_soll_stunden_nach_stundenplan(
        self, eintraege: list[ZeiteintragsDTO]
    ) -> None:
        """Ordnet Stundenplan-Soll zeilenweise zu; Rest-Soll auf die letzte Zeile."""
        for eintrag in eintraege:
            eintrag.soll_stunden_nach_Stundenplan = None
        if not eintraege or eintraege[0].ist_feiertag:
            return

        bloecke = self._stundenplan_bloecke_fuer_datum(eintraege[0].datum)
        if not bloecke:
            return

        n = len(eintraege)
        m = len(bloecke)
        sekunden: list[int] = [0] * n

        for i in range(min(n, m)):
            sekunden[i] = self._netto_arbeitssekunden(bloecke[i])

        if n < m:
            sekunden[n - 1] += sum(
                self._netto_arbeitssekunden(b) for b in bloecke[n:]
            )

        for eintrag, sek in zip(eintraege, sekunden, strict=True):
            if sek > 0:
                eintrag.soll_stunden_nach_Stundenplan = self._sekunden_als_uhrzeit_fuer_dauer(
                    sek
                )

    def set_vertrag_stunden_nach_wochentag(self, mapping: dict[int, str]) -> None:
        """Setzt das Mapping von Wochentag zu Vertragsarbeitszeit (z.B. {1: '08:00', ...})."""
        self._vertrag_stunden_nach_wochentag = dict(mapping)

    def set_sollstunden_an_feiertagen(self, aktiv: bool) -> None:
        """Ob Vertrags-Soll an Feiertagen angezeigt wird ([sollstunden].sollstunden_an_feiertagen)."""
        self._sollstunden_an_feiertagen = aktiv

    def set_kommentar_urlaubstage(self, text: str) -> None:
        """Praefix/Kuerzel fuer Kommentar an Urlaubstagen ([sollstunden].kommentar_urlaubstage)."""
        self._kommentar_urlaubstage = text.strip()

    def set_kommentar_krankheitstage(self, text: str) -> None:
        """Praefix/Kuerzel fuer Kommentar an Krankheitstagen ([sollstunden].kommentar_krankheitstage)."""
        self._kommentar_krankheitstage = text.strip()

    def set_kommentar_ueberstunden_frei(self, text: str) -> None:
        """Kommentar bei uhrzeit_von = uhrzeit_bis ([sollstunden].kommentar_ueberstunden_frei)."""
        t = text.strip()
        self._kommentar_ueberstunden_frei = t if t else "Überstunden frei"

    def _ist_ueberstunden_frei_zeitraum(self, eintrag: ZeiteintragsDTO) -> bool:
        return (
            eintrag.uhrzeit_von is not None
            and eintrag.uhrzeit_bis is not None
            and eintrag.uhrzeit_von == eintrag.uhrzeit_bis
        )

    def _kuerze_anmerkung(self, text: str) -> str:
        return text[: self._MAX_ANMERKUNG_LAENGE]

    def _wende_kommentar_praefix(
        self, eintrag: ZeiteintragsDTO, prefix: str, bestehend: str
    ) -> None:
        if not prefix:
            return
        prefix_mit_trenner = f"{prefix}: "
        prefix_mit_punkt_legacy = f"{prefix}."
        if not bestehend:
            eintrag.anmerkung = self._kuerze_anmerkung(prefix)
        elif (
            bestehend == prefix
            or bestehend.startswith(prefix_mit_trenner)
            or bestehend.startswith(prefix_mit_punkt_legacy)
        ):
            return
        else:
            eintrag.anmerkung = self._kuerze_anmerkung(f"{prefix_mit_trenner}{bestehend}")

    def _wende_kommentar_regeln_an(self, eintrag: ZeiteintragsDTO) -> None:
        """Ueberstunden-frei; Feiertagsname; Krank (K) vor Urlaub (U), jeweils gemaess Config."""
        if self._ist_ueberstunden_frei_zeitraum(eintrag):
            eintrag.anmerkung = self._kuerze_anmerkung(self._kommentar_ueberstunden_frei)
            return

        bestehend = (eintrag.anmerkung or "").strip()
        if eintrag.ist_feiertag and not bestehend:
            name = (eintrag.feiertagsname or "").strip()
            if name:
                eintrag.anmerkung = self._kuerze_anmerkung(name)
                bestehend = eintrag.anmerkung

        if eintrag.ist_feiertag:
            return

        if eintrag.ist_krank:
            if self._sondertag_kommentar_erlaubt(eintrag.datum):
                self._wende_kommentar_praefix(
                    eintrag, self._kommentar_krankheitstage, bestehend
                )
            return

        if eintrag.ist_urlaub and self._sondertag_kommentar_erlaubt(eintrag.datum):
            self._wende_kommentar_praefix(eintrag, self._kommentar_urlaubstage, bestehend)

    def _sondertag_kommentar_erlaubt(self, datum: date) -> bool:
        """Kuerzel im Kommentar nur Mo–Fr mit Vertrags-Soll > 0 (Urlaub/Krank)."""
        if datum.isoweekday() >= 6:
            return False
        return self._berechne_soll_stunden_nach_vertrag(datum) is not None

    def _ist_krank_oder_urlaub_tag(self, eintrag: ZeiteintragsDTO) -> bool:
        return eintrag.ist_krank or eintrag.ist_urlaub

    def _eintrag_hat_geleistete_arbeitszeit(self, eintrag: ZeiteintragsDTO) -> bool:
        if eintrag.uhrzeit_von is None or eintrag.uhrzeit_bis is None:
            return False
        if eintrag.uhrzeit_von >= eintrag.uhrzeit_bis:
            return False
        return self._netto_arbeitssekunden(eintrag) > 0

    def _tag_hat_geleistete_arbeitszeit(self, eintraege: list[ZeiteintragsDTO]) -> bool:
        return any(self._eintrag_hat_geleistete_arbeitszeit(e) for e in eintraege)

    def _setze_soll_stundenplan_wie_vertrag(self, eintraege: list[ZeiteintragsDTO]) -> None:
        for eintrag in eintraege:
            eintrag.soll_stunden_nach_Stundenplan = eintrag.soll_stunden_nach_vertrag

    def _berechne_soll_stunden_nach_vertrag(self, datum: date) -> time | None:
        """Soll-Arbeitszeit nach Vertrag: config.toml ([sollstunden].wochenstunden), je Wochentag."""
        if not self._sollstunden_an_feiertagen and any(
            f.datum == datum for f in self.feiertage
        ):
            return None
        soll_str = self._vertrag_stunden_nach_wochentag.get(datum.isoweekday(), "").strip()
        if not soll_str:
            return None

        parsed = self._parse_soll_zeit_aus_string(soll_str)
        if parsed is None:
            return None
        if parsed.hour == 0 and parsed.minute == 0 and parsed.second == 0:
            return None
        return parsed
    
    def _parse_soll_zeit_aus_string(self, zeit_str: str) -> time | None:
        """Konvertiert einen Zeit-String (z.B. '4:00', '04:00', '8:30') zu time Objekt."""
        try:
            zeit_str = zeit_str.strip()
            if not zeit_str:
                return None
            
            # Versuche standardisierte Formate zuerst
            for fmt in ("%H:%M:%S", "%H:%M"):
                try:
                    dt = datetime.strptime(zeit_str, fmt)
                    return dt.time()
                except ValueError:
                    continue
            
            # Falls kein Format passt, versuche manuelles Parsing (für Formate wie "4:00")
            parts = zeit_str.split(":")
            if len(parts) >= 2:
                try:
                    h = int(parts[0])
                    m = int(parts[1])
                    s = int(parts[2]) if len(parts) > 2 else 0
                    if 0 <= h < 24 and 0 <= m < 60 and 0 <= s < 60:
                        return time(h, m, s)
                except (ValueError, IndexError):
                    pass
            
            return None
        except Exception:
            return None

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

        return eintrag

    def _berechne_geleistete_stunden_aus_zeiten(
        self, eintrag: ZeiteintragsDTO
    ) -> time | None:
        if not self._eintrag_hat_geleistete_arbeitszeit(eintrag):
            return None
        return self._sekunden_als_uhrzeit_fuer_dauer(
            self._netto_arbeitssekunden(eintrag)
        )

    def _summe_arbeitssekunden_am_tag(self, eintraege: list[ZeiteintragsDTO]) -> int:
        return sum(
            self._netto_arbeitssekunden(e)
            for e in eintraege
            if self._eintrag_hat_geleistete_arbeitszeit(e)
        )

    def _berechne_geleistete_stunden_zeile_1_vertrag_plus_arbeit(
        self,
        eintraege: list[ZeiteintragsDTO],
        *,
        hat_arbeit: bool,
        vertrag_soll: time | None,
    ) -> time | None:
        """
        Urlaub/Krank Zeile 1 (Geleistet-Spalte): Soll nach Vertrag;
        bei zusaetzlicher Arbeitszeit Vertrag + Summe aller Arbeitszeiten des Tages.
        """
        if not hat_arbeit:
            return vertrag_soll
        vertrag_sek = (
            self._sekunden_seit_mitternacht(vertrag_soll) if vertrag_soll is not None else 0
        )
        gesamt_sek = vertrag_sek + self._summe_arbeitssekunden_am_tag(eintraege)
        if gesamt_sek <= 0:
            return None
        return self._sekunden_als_uhrzeit_fuer_dauer(gesamt_sek)

    def _aktualisiere_geleistete_stunden_fuer_tag(
        self, eintraege: list[ZeiteintragsDTO]
    ) -> None:
        if not eintraege:
            return
        ist_urlaub = eintraege[0].ist_urlaub
        ist_krank = eintraege[0].ist_krank
        hat_arbeit = self._tag_hat_geleistete_arbeitszeit(eintraege)
        vertrag_soll = None
        if ist_urlaub or ist_krank:
            vertrag_soll = self._berechne_soll_stunden_nach_vertrag(eintraege[0].datum)
        for zeile_nr, eintrag in enumerate(eintraege, start=1):
            if (ist_krank or ist_urlaub) and zeile_nr == 1:
                eintrag.geleistete_stunden = (
                    self._berechne_geleistete_stunden_zeile_1_vertrag_plus_arbeit(
                        eintraege,
                        hat_arbeit=hat_arbeit,
                        vertrag_soll=vertrag_soll,
                    )
                )
            else:
                eintrag.geleistete_stunden = self._berechne_geleistete_stunden_aus_zeiten(
                    eintrag
                )

    def _setze_soll_felder_fuer_tag(self, eintraege: list[ZeiteintragsDTO]) -> None:
        """Vertrag-Soll Zeile 1; bei Krank/Urlaub Stundenplan-Soll = Vertrag-Soll ohne Arbeitszeit."""
        if not eintraege:
            return
        if self._ist_krank_oder_urlaub_tag(eintraege[0]):
            vertrag_soll = self._berechne_soll_stunden_nach_vertrag(eintraege[0].datum)
            for i, eintrag in enumerate(eintraege):
                if i == 0:
                    eintrag.soll_stunden_nach_vertrag = vertrag_soll
                else:
                    eintrag.soll_stunden_nach_vertrag = None
            if self._tag_hat_geleistete_arbeitszeit(eintraege):
                self._verteile_soll_stunden_nach_stundenplan(eintraege)
            else:
                self._setze_soll_stundenplan_wie_vertrag(eintraege)
            return
        for i, eintrag in enumerate(eintraege):
            if i == 0:
                eintrag.soll_stunden_nach_vertrag = self._berechne_soll_stunden_nach_vertrag(
                    eintrag.datum
                )
            else:
                eintrag.soll_stunden_nach_vertrag = None
        self._verteile_soll_stunden_nach_stundenplan(eintraege)

    def _basiseintrag_aus_zeiteintrag(self, eintrag: Zeiteintrag) -> ZeiteintragsDTO:
        return ZeiteintragsDTO(
            id=eintrag.id,
            datum=eintrag.datum,
            uhrzeit_von=eintrag.uhrzeit_von,
            uhrzeit_bis=eintrag.uhrzeit_bis,
            pause_beginn=eintrag.pause_beginn,
            pause_ende=eintrag.pause_ende,
            pause2_beginn=eintrag.pause2_beginn,
            pause2_ende=eintrag.pause2_ende,
            anmerkung=eintrag.anmerkung,
        )

    def _leerer_eintrag_dto(self, datum: date) -> ZeiteintragsDTO:
        dto = self._initialisiere_dto(ZeiteintragsDTO(
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
        self.anreichere_eintraege_fuer_tag([dto])
        return dto

    def _zeiteintrag_zu_dto(self, eintrag: Zeiteintrag) -> ZeiteintragsDTO:
        jahr = eintrag.datum.year
        self._initialisiere_jahresdaten(jahr)
        dto = self._initialisiere_dto(self._basiseintrag_aus_zeiteintrag(eintrag))
        self.anreichere_eintraege_fuer_tag([dto])
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



