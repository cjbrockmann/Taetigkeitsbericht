from __future__ import annotations

from datetime import date, time

from Core.Domain.models.models_worktime import Stundenplan
from test.support.factories import feiertag, zeiteintrags_dto
from test.support.fakes import dto_anwendung


def test_info_aus_stundenplan_am_wochentag():
    montag = date(2025, 3, 10)
    plan = Stundenplan(
        id=1,
        mandant_id=1,
        wochentag=1,
        uhrzeit_von=time(8, 0),
        uhrzeit_bis=time(12, 0),
        anmerkung="Buero",
    )
    app = dto_anwendung(stundenplan=[plan])
    dto = zeiteintrags_dto(datum=montag)
    app.anreichere_eintraege_fuer_tag([dto])
    assert dto.info == "Buero"


def test_info_zweite_zeile_zweiter_stundenplan_block():
    montag = date(2025, 3, 10)
    plan1 = Stundenplan(
        id=1,
        mandant_id=1,
        wochentag=1,
        uhrzeit_von=time(8, 0),
        uhrzeit_bis=time(12, 0),
        anmerkung="Vormittag",
    )
    plan2 = Stundenplan(
        id=2,
        mandant_id=1,
        wochentag=1,
        uhrzeit_von=time(13, 0),
        uhrzeit_bis=time(17, 0),
        anmerkung="Nachmittag",
    )
    app = dto_anwendung(stundenplan=[plan2, plan1])
    zeile1 = zeiteintrags_dto(datum=montag)
    zeile2 = zeiteintrags_dto(datum=montag)
    app.anreichere_eintraege_fuer_tag([zeile1, zeile2])
    assert zeile1.info == "Vormittag"
    assert zeile2.info == "Nachmittag"


def test_info_leer_am_wochenende():
    samstag = date(2025, 3, 8)
    plan = Stundenplan(
        id=1,
        mandant_id=1,
        wochentag=6,
        uhrzeit_von=time(8, 0),
        uhrzeit_bis=time(12, 0),
        anmerkung="Samstag",
    )
    app = dto_anwendung(stundenplan=[plan])
    dto = zeiteintrags_dto(datum=samstag)
    app.anreichere_eintraege_fuer_tag([dto])
    assert dto.info is None


def test_info_leer_an_feiertag():
    feiertag_datum = date(2025, 1, 1)
    plan = Stundenplan(
        id=1,
        mandant_id=1,
        wochentag=3,
        uhrzeit_von=time(8, 0),
        uhrzeit_bis=time(12, 0),
        anmerkung="Neujahr",
    )
    app = dto_anwendung(
        feiertage=[feiertag(feiertag_datum, "Neujahr")],
        stundenplan=[plan],
    )
    dto = zeiteintrags_dto(datum=feiertag_datum)
    app.anreichere_eintraege_fuer_tag([dto])
    assert dto.info is None
