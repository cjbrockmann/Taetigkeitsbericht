from __future__ import annotations

from datetime import date, time

from test.support.factories import urlaub, zeiteintrag, zeiteintrags_dto
from test.support.fakes import dto_anwendung


def test_netto_arbeitszeit_acht_stunden():
    app = dto_anwendung()
    eintrag = zeiteintrag(
        uhrzeit_von=time(8, 0),
        uhrzeit_bis=time(16, 0),
    )
    sek = app._netto_arbeitssekunden(eintrag)
    assert sek == 8 * 3600


def test_parse_soll_zeit_aus_string():
    app = dto_anwendung()
    assert app._parse_soll_zeit_aus_string("8:30") == time(8, 30)
    assert app._parse_soll_zeit_aus_string("08:30:00") == time(8, 30, 0)
    assert app._parse_soll_zeit_aus_string("") is None


def test_urlaub_erste_zeile_geleistet_vertrag_soll():
    montag = date(2025, 3, 10)
    app = dto_anwendung(urlaub=[urlaub(montag, montag)])
    dto = zeiteintrags_dto(datum=montag)
    app.anreichere_eintraege_fuer_tag([dto])
    assert dto.geleistete_stunden == time(8, 0, 0)
    assert dto.soll_stunden_nach_vertrag == time(8, 0, 0)


def test_liste_im_monat_fuellt_leere_tage():
    app = dto_anwendung(
        zeiteintraege=[zeiteintrag(datum=date(2025, 3, 5))],
    )
    liste = app.liste_im_monat(1, 2025, 3)
    assert len(liste) == 31
    mit_inhalt = [e for e in liste if e.uhrzeit_von is not None]
    assert len(mit_inhalt) == 1
