from __future__ import annotations

from datetime import time

from External.Presentation.Desktop.arbeitszeit_berechnung import (
    minuten_als_hh_mm,
    netto_arbeitsminuten,
    parse_uhrzeit_minuten,
    zeit_aus_text,
)


def test_parse_uhrzeit_hh_mm():
    assert parse_uhrzeit_minuten("08:30") == 8 * 60 + 30
    assert parse_uhrzeit_minuten("8.30") == 8 * 60 + 30


def test_zeit_aus_text():
    assert zeit_aus_text("16:45") == time(16, 45)


def test_netto_arbeitsminuten_mit_pause():
    netto = netto_arbeitsminuten(
        "08:00",
        "16:00",
        "12:00",
        "12:30",
    )
    assert netto == 7 * 60 + 30


def test_netto_arbeitsminuten_bis_vor_von():
    assert netto_arbeitsminuten("16:00", "08:00", "", "") is None


def test_minuten_als_hh_mm():
    assert minuten_als_hh_mm(90) == "01:30"
