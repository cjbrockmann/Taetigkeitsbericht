from __future__ import annotations

from datetime import date, time
from uuid import uuid4

from Core.Domain.models.models_worktime import Stundenplan, Zeiteintrag
from test.support.fakes import dto_anwendung


def _eintrag(
    datum: date,
    *,
    von: time | None = None,
    bis: time | None = None,
    mandant_id: int = 1,
) -> Zeiteintrag:
    return Zeiteintrag(
        id=uuid4(),
        mandant_id=mandant_id,
        datum=datum,
        uhrzeit_von=von or time(8, 0),
        uhrzeit_bis=bis or time(16, 0),
    )


def _stundenplan_mo_bis_fr() -> list[Stundenplan]:
    return [
        Stundenplan(
            mandant_id=1,
            wochentag=tag,
            uhrzeit_von=time(8, 0),
            uhrzeit_bis=time(16, 0),
        )
        for tag in range(1, 6)
    ]


def test_guthaben_verrechnen_persistiert_monatsende_und_folgevormonat() -> None:
    app = dto_anwendung(
        zeiteintraege=[
            _eintrag(date(2026, 3, 2)),
            _eintrag(date(2026, 3, 3)),
        ],
        stundenplan=_stundenplan_mo_bis_fr(),
        mandant_id=1,
    )
    ergebnis = app.guthaben_verrechnen(1, 2026, 3)

    assert ergebnis.ist_stunden == 16.0
    assert ergebnis.soll_stundenplan_stunden == 16.0
    assert ergebnis.soll_vertrag_stunden == 16.0
    assert ergebnis.saldo_stunden == 0.0
    assert ergebnis.guthaben_monat_stunden == 0.0

    assert app.guthaben_stunden_laufender_monat is not None
    assert app.guthaben_stunden_laufender_monat.datum == date(2026, 3, 1)
    assert app.guthaben_stunden_laufender_monat.stunden_guthaben_monatsende_aktuell == 0.0

    guthaben = app._guthaben_helper._guthaben_stunden_anwendung
    folge = guthaben.hole_fuer_monat(1, date(2026, 4, 1))
    assert folge is not None
    assert folge.stunden_guthaben_vormonat == 0.0


def test_guthaben_verrechnen_schreibt_kein_manuell_bei_ueberstunden() -> None:
    app = dto_anwendung(
        zeiteintraege=[_eintrag(date(2026, 3, 10), von=time(8, 0), bis=time(18, 0))],
        stundenplan=_stundenplan_mo_bis_fr(),
        mandant_id=1,
    )
    app.guthaben_verrechnen(1, 2026, 3)
    guthaben = app._guthaben_helper._guthaben_stunden_anwendung
    maerz = guthaben.hole_fuer_monat(1, date(2026, 3, 1))
    april = guthaben.hole_fuer_monat(1, date(2026, 4, 1))
    assert maerz is not None
    assert april is not None
    assert maerz.stunden_guthaben_monatsende_aktuell == 2.0
    assert maerz.stunden_guthaben_vormonat_manuell is None
    assert april.stunden_guthaben_vormonat == 2.0
    assert april.stunden_guthaben_vormonat_manuell is None


def test_guthaben_verrechnen_mit_ueberstunden() -> None:
    app = dto_anwendung(
        zeiteintraege=[_eintrag(date(2026, 3, 10), von=time(8, 0), bis=time(18, 0))],
        stundenplan=_stundenplan_mo_bis_fr(),
        mandant_id=1,
    )
    ergebnis = app.guthaben_verrechnen(1, 2026, 3)

    assert ergebnis.ist_stunden == 10.0
    assert ergebnis.soll_stundenplan_stunden == 8.0
    assert ergebnis.soll_vertrag_stunden == 8.0
    assert ergebnis.guthaben_monat_stunden == 2.0

    assert (
        app.guthaben_stunden_laufender_monat is not None
        and app.guthaben_stunden_laufender_monat.stunden_guthaben_monatsende_aktuell
        == 2.0
    )
    guthaben = app._guthaben_helper._guthaben_stunden_anwendung
    folge = guthaben.hole_fuer_monat(1, date(2026, 4, 1))
    assert folge is not None
    assert folge.stunden_guthaben_vormonat == 2.0


def test_aktualisiere_guthaben_im_monat_persistiert_nach_zeiteintrag() -> None:
    app = dto_anwendung(
        zeiteintraege=[_eintrag(date(2026, 3, 10), von=time(8, 0), bis=time(18, 0))],
        stundenplan=_stundenplan_mo_bis_fr(),
        mandant_id=1,
    )
    app.aktualisiere_guthaben_im_monat(1, 2026, 3)
    gs = app._guthaben_helper._guthaben_stunden_anwendung.hole_fuer_monat(1, date(2026, 3, 1))
    assert gs is not None
    assert gs.stunden_guthaben_monatsende_aktuell == 2.0


def test_guthaben_verrechnen_persistiert_defizit_negativ_und_nicht_in_manuell() -> None:
    app = dto_anwendung(
        zeiteintraege=[_eintrag(date(2026, 3, 10), von=time(8, 0), bis=time(12, 0))],
        stundenplan=_stundenplan_mo_bis_fr(),
        mandant_id=1,
    )
    ergebnis = app.guthaben_verrechnen(1, 2026, 3)
    assert ergebnis.defizit_monat_stunden == 4.0
    assert ergebnis.saldo_stunden == -4.0
    guthaben = app._guthaben_helper._guthaben_stunden_anwendung
    maerz = guthaben.hole_fuer_monat(1, date(2026, 3, 1))
    april = guthaben.hole_fuer_monat(1, date(2026, 4, 1))
    assert maerz is not None
    assert april is not None
    assert maerz.stunden_guthaben_monatsende_aktuell == -4.0
    assert maerz.stunden_guthaben_vormonat_manuell is None
    assert april.stunden_guthaben_vormonat == -4.0
    assert april.stunden_guthaben_vormonat_manuell is None


def test_liste_im_monat_mit_guthaben_liefert_eintraege_und_guthaben() -> None:
    app = dto_anwendung(
        zeiteintraege=[_eintrag(date(2026, 3, 10), von=time(8, 0), bis=time(18, 0))],
        stundenplan=_stundenplan_mo_bis_fr(),
        mandant_id=1,
    )
    monat = app.liste_im_monat_mit_guthaben(1, 2026, 3)

    assert len(monat.eintraege) == 31
    assert monat.guthaben.datum == date(2026, 3, 1)
    assert monat.guthaben.verrechnung.guthaben_monat_stunden == 2.0
    assert monat.guthaben.datensatz is not None
    assert monat.guthaben.datensatz.stunden_guthaben_monatsende_aktuell == 2.0
    assert app.guthaben_stunden_laufender_monat is monat.guthaben.datensatz
