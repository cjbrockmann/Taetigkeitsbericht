from __future__ import annotations

from datetime import date, time

import pytest

from test.support.factories import feiertag, krank, urlaub, zeiteintrags_dto
from test.support.fakes import dto_anwendung


def test_kommentar_modus_ungueltig_wird_kuerzel(dto_app):
    dto_app.set_kommentar_urlaub_krank_modus("ungueltig")
    assert dto_app._kommentar_urlaub_krank_modus == "kuerzel"


def test_kommentar_modus_prefix_alias_praefix(dto_app):
    dto_app.set_kommentar_urlaub_krank_modus("prefix")
    assert dto_app._kommentar_urlaub_krank_modus == "praefix"


def test_urlaub_ohne_arbeitszeit_nur_kuerzel():
    montag = date(2025, 3, 10)
    app = dto_anwendung(urlaub=[urlaub(montag, montag)])
    dto = zeiteintrags_dto(datum=montag)
    app.anreichere_eintraege_fuer_tag([dto])
    assert dto.anmerkung == "U"


def test_urlaub_mit_arbeitszeit_praefix_modus():
    montag = date(2025, 3, 10)
    app = dto_anwendung(urlaub=[urlaub(montag, montag)])
    app.set_kommentar_urlaub_krank_modus("praefix")
    dto = zeiteintrags_dto(
        datum=montag,
        uhrzeit_von=time(8, 0),
        uhrzeit_bis=time(12, 0),
        anmerkung="Meeting",
    )
    app.anreichere_eintraege_fuer_tag([dto])
    assert dto.anmerkung == "U: Meeting"


def test_urlaub_kuerzel_modus():
    montag = date(2025, 3, 10)
    app = dto_anwendung(urlaub=[urlaub(montag, montag)])
    app.set_kommentar_urlaub_krank_modus("kuerzel")
    dto = zeiteintrags_dto(
        datum=montag,
        uhrzeit_von=time(8, 0),
        uhrzeit_bis=time(12, 0),
        anmerkung="wird ueberschrieben",
    )
    app.anreichere_eintraege_fuer_tag([dto])
    assert dto.anmerkung == "U"


def test_ueberstunden_frei_setzt_kommentar_und_geleistet_null():
    montag = date(2025, 3, 10)
    app = dto_anwendung()
    app.set_kommentar_ueberstunden_frei("Frei")
    dto = zeiteintrags_dto(
        datum=montag,
        uhrzeit_von=time(12, 0),
        uhrzeit_bis=time(12, 0),
    )
    app.anreichere_eintraege_fuer_tag([dto])
    assert dto.anmerkung == "Frei"
    assert dto.geleistete_stunden == time(0, 0, 0)


def test_feiertag_ohne_anmerkung_bekommt_namen():
    tag = date(2025, 1, 1)
    app = dto_anwendung(feiertage=[feiertag(tag, "Neujahr")])
    dto = zeiteintrags_dto(datum=tag)
    app.anreichere_eintraege_fuer_tag([dto])
    assert dto.anmerkung == "Neujahr"
    assert dto.ist_feiertag is True


def test_urlaub_am_samstag_kein_kuerzel_im_kommentar():
    samstag = date(2025, 3, 8)
    app = dto_anwendung(urlaub=[urlaub(samstag, samstag)])
    dto = zeiteintrags_dto(datum=samstag)
    app.anreichere_eintraege_fuer_tag([dto])
    assert dto.ist_urlaub is True
    assert dto.anmerkung in (None, "")
