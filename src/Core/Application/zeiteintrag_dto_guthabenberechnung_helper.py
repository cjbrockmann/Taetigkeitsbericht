from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time

from Core.Application.guthaben_stunden_anwendung import GuthabenStundenAnwendung
from Core.Domain.models.models_worktime import GuthabenStunden, ZeiteintragsDTO


@dataclass(frozen=True)
class GuthabenVerrechnungErgebnis:
    """Ergebnis der Monats-Verrechnung (Ist/Soll/Vormonat → Zeitguthaben oder -defizit)."""

    ist_stunden: float
    guthaben_vormonat_stunden: float
    defizit_vormonat_stunden: float
    soll_stundenplan_stunden: float
    soll_vertrag_stunden: float
    saldo_stunden: float
    guthaben_monat_stunden: float
    defizit_monat_stunden: float

    @staticmethod
    def stunden_als_hh_mm(stunden: float) -> str:
        minuten = int(round(max(0.0, stunden) * 60))
        h, m = divmod(minuten, 60)
        return f"{h:02d}:{m:02d}"


@dataclass(frozen=True)
class GuthabenAmMonatsanfang:
    """Guthaben-/Überstunden-Verrechnung zum 1. des Monats (inkl. persistiertem DB-Datensatz)."""

    datum: date
    verrechnung: GuthabenVerrechnungErgebnis
    datensatz: GuthabenStunden | None


@dataclass(frozen=True)
class ZeiteintragMonatMitGuthaben:
    """Monatszeilen plus angebundene Guthabenberechnung."""

    eintraege: list[ZeiteintragsDTO]
    guthaben: GuthabenAmMonatsanfang


class ZeiteintragDtoGuthabenberechnungHelper:
    """Zeitguthaben-Verrechnung und Persistenz in guthaben_stunden (ohne DI)."""

    def __init__(self, guthaben_stunden_anwendung: GuthabenStundenAnwendung) -> None:
        self._guthaben_stunden_anwendung = guthaben_stunden_anwendung
        self.guthaben_stunden_laufender_monat: GuthabenStunden | None = None

    def monat_mit_guthaben(
        self,
        mandant_id: int,
        jahr: int,
        monat: int,
        eintraege: list[ZeiteintragsDTO],
        *,
        persistieren: bool = True,
    ) -> ZeiteintragMonatMitGuthaben:
        monatserster = date(jahr, monat, 1)
        if persistieren:
            verrechnung = self.guthaben_verrechnen(
                mandant_id, jahr, monat, eintraege=eintraege
            )
            datensatz = self.guthaben_stunden_laufender_monat
        else:
            verrechnung = self.berechne_guthaben_verrechnung(
                mandant_id, jahr, monat, eintraege
            )
            datensatz = self._guthaben_stunden_anwendung.hole_fuer_monat(
                mandant_id, monatserster
            )
        return ZeiteintragMonatMitGuthaben(
            eintraege=eintraege,
            guthaben=GuthabenAmMonatsanfang(
                datum=monatserster,
                verrechnung=verrechnung,
                datensatz=datensatz,
            ),
        )

    def guthaben_verrechnen(
        self,
        mandant_id: int,
        jahr: int,
        monat: int,
        *,
        eintraege: list[ZeiteintragsDTO],
    ) -> GuthabenVerrechnungErgebnis:
        """
        Verrechnet Zeitguthaben/-defizit und persistiert den Saldo vorzeichenbehaftet:

        - Am 1. des laufenden Monats: ``stunden_guthaben_monatsende_aktuell``
          (positiv = Guthaben, negativ = Defizit).
        - Am 1. des Folgemonats: ``stunden_guthaben_vormonat`` = derselbe Saldo.

        ``stunden_guthaben_vormonat_manuell`` wird nie berechnet, nur bei bestehendem
        Datensatz unverändert übernommen (manuelle Korrektur per Formular).
        """
        monatserster = date(jahr, monat, 1)
        folge_jahr, folge_monat = _naechster_monat(jahr, monat)
        folgemonatserster = date(folge_jahr, folge_monat, 1)

        eintrag_aktuell = self._guthaben_stunden_anwendung.hole_fuer_monat(
            mandant_id, monatserster
        )
        self.guthaben_stunden_laufender_monat = eintrag_aktuell

        ergebnis = self.berechne_guthaben_verrechnung(
            mandant_id, jahr, monat, eintraege, eintrag_aktuell=eintrag_aktuell
        )
        saldo_monat = ergebnis.saldo_stunden
        saldo_vormonat = _lese_saldo_vormonat(
            self._guthaben_stunden_anwendung,
            mandant_id,
            monatserster,
            eintrag_aktuell,
        )
        gespeichert_aktuell = self._speichere_guthaben_stunden(
            GuthabenStunden(
                id=eintrag_aktuell.id if eintrag_aktuell else None,
                mandant_id=mandant_id,
                datum=monatserster,
                stunden_guthaben_vormonat=saldo_vormonat,
                stunden_guthaben_vormonat_manuell=_manuell_aus_datensatz(
                    eintrag_aktuell
                ),
                stunden_guthaben_monatsende_aktuell=saldo_monat,
            )
        )
        self.guthaben_stunden_laufender_monat = gespeichert_aktuell

        eintrag_folge = self._guthaben_stunden_anwendung.hole_fuer_monat(
            mandant_id, folgemonatserster
        )
        self._speichere_guthaben_stunden(
            GuthabenStunden(
                id=eintrag_folge.id if eintrag_folge else None,
                mandant_id=mandant_id,
                datum=folgemonatserster,
                stunden_guthaben_vormonat=saldo_monat,
                stunden_guthaben_vormonat_manuell=_manuell_aus_datensatz(eintrag_folge),
                stunden_guthaben_monatsende_aktuell=(
                    eintrag_folge.stunden_guthaben_monatsende_aktuell
                    if eintrag_folge
                    else 0.0
                ),
            )
        )

        return ergebnis

    def berechne_guthaben_verrechnung(
        self,
        mandant_id: int,
        jahr: int,
        monat: int,
        eintraege: list[ZeiteintragsDTO],
        *,
        eintrag_aktuell: GuthabenStunden | None = None,
    ) -> GuthabenVerrechnungErgebnis:
        monatserster = date(jahr, monat, 1)
        if eintrag_aktuell is None:
            eintrag_aktuell = self._guthaben_stunden_anwendung.hole_fuer_monat(
                mandant_id, monatserster
            )
        ist, soll_sp, soll_vertrag = _summen_stunden_aus_monatseintraegen(eintraege)
        saldo_vormonat = _lese_saldo_vormonat(
            self._guthaben_stunden_anwendung,
            mandant_id,
            monatserster,
            eintrag_aktuell,
        )
        guthaben_v, defizit_v = _saldo_zu_guthaben_und_defizit(saldo_vormonat)
        saldo = ist + saldo_vormonat - soll_vertrag
        guthaben_monat, defizit_monat = _saldo_zu_guthaben_und_defizit(saldo)
        return GuthabenVerrechnungErgebnis(
            ist_stunden=ist,
            guthaben_vormonat_stunden=guthaben_v,
            defizit_vormonat_stunden=defizit_v,
            soll_stundenplan_stunden=soll_sp,
            soll_vertrag_stunden=soll_vertrag,
            saldo_stunden=saldo,
            guthaben_monat_stunden=guthaben_monat,
            defizit_monat_stunden=defizit_monat,
        )

    def _speichere_guthaben_stunden(self, eintrag: GuthabenStunden) -> GuthabenStunden:
        return self._guthaben_stunden_anwendung.erfasse(eintrag)


def _naechster_monat(jahr: int, monat: int) -> tuple[int, int]:
    if monat == 12:
        return jahr + 1, 1
    return jahr, monat + 1


def _vorheriger_monat(jahr: int, monat: int) -> tuple[int, int]:
    if monat == 1:
        return jahr - 1, 12
    return jahr, monat - 1


def _sekunden_seit_mitternacht(t: time) -> int:
    return t.hour * 3600 + t.minute * 60 + t.second


def _time_zu_dezimalstunden(wert: time | None) -> float:
    if wert is None:
        return 0.0
    return _sekunden_seit_mitternacht(wert) / 3600.0


def _summen_stunden_aus_monatseintraegen(
    eintraege: list[ZeiteintragsDTO],
) -> tuple[float, float, float]:
    """
    Summen für die Guthaben-Verrechnung (nur Tage mit persistierten Zeiteinträgen).

    Saldo nutzt ausschließlich Soll nach Vertrag. Soll nach Stundenplan wird nur für
    die Anzeige im Ergebnis (Fußzeile) mitgeführt.
    """
    tage_mit_erfassung = {e.datum for e in eintraege if e.id is not None}
    ist = 0.0
    soll_sp = 0.0
    soll_vertrag = 0.0
    nach_tag: dict[date, list[ZeiteintragsDTO]] = {}
    for eintrag in eintraege:
        if eintrag.datum in tage_mit_erfassung:
            nach_tag.setdefault(eintrag.datum, []).append(eintrag)

    for tages_eintraege in nach_tag.values():
        tag_ist = 0.0
        tag_sp = 0.0
        tag_vertrag = 0.0
        for eintrag in tages_eintraege:
            tag_ist += _time_zu_dezimalstunden(eintrag.geleistete_stunden)
            tag_sp += _time_zu_dezimalstunden(eintrag.soll_stunden_nach_Stundenplan)
            if eintrag.soll_stunden_nach_vertrag is not None:
                tag_vertrag += _time_zu_dezimalstunden(eintrag.soll_stunden_nach_vertrag)
        ist += tag_ist
        soll_sp += tag_sp
        soll_vertrag += tag_vertrag

    return ist, soll_sp, soll_vertrag


def _manuell_aus_datensatz(eintrag: GuthabenStunden | None) -> float | None:
    """Nur bestehende manuelle Korrektur übernehmen, nie berechnen."""
    if eintrag is None:
        return None
    return eintrag.stunden_guthaben_vormonat_manuell


def _saldo_zu_guthaben_und_defizit(saldo: float) -> tuple[float, float]:
    """Darstellung: Guthaben und Defizit getrennt, DB speichert den Saldo."""
    return max(0.0, saldo), max(0.0, -saldo)


def _lese_saldo_vormonat(
    guthaben_anwendung: GuthabenStundenAnwendung,
    mandant_id: int,
    monatserster: date,
    eintrag_aktuell: GuthabenStunden | None,
) -> float:
    """
    Vorzeichen-Saldo für die Verrechnung (positiv = Guthaben, negativ = Defizit).

    Aus ``stunden_guthaben_vormonat`` bzw. Vormonats-``monatsende_aktuell``;
    ``stunden_guthaben_vormonat_manuell`` überschreibt nur bei manueller Korrektur
    (als positiver Guthaben-Wert).
    """
    if eintrag_aktuell is not None:
        manuell = eintrag_aktuell.stunden_guthaben_vormonat_manuell
        if manuell is not None:
            return manuell
        return eintrag_aktuell.stunden_guthaben_vormonat
    vjahr, vmonat = _vorheriger_monat(monatserster.year, monatserster.month)
    vorher = guthaben_anwendung.hole_fuer_monat(mandant_id, date(vjahr, vmonat, 1))
    if vorher is None:
        return 0.0
    return vorher.stunden_guthaben_monatsende_aktuell
