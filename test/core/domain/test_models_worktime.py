from __future__ import annotations

from datetime import date, time

import pytest
from pydantic import ValidationError

from Core.Domain.models.models_worktime import (
    Krankmeldung,
    Urlaubsantrag,
    Zeiteintrag,
    ZeiteintragsDTO,
)


def test_zeiteintrag_pause_muss_im_arbeitszeitfenster_liegen():
    with pytest.raises(ValidationError, match="pause_beginn"):
        Zeiteintrag(
            datum=date(2025, 1, 10),
            uhrzeit_von=time(8, 0),
            uhrzeit_bis=time(16, 0),
            pause_beginn=time(7, 0),
            pause_ende=time(7, 30),
        )


def test_zeiteintrag_ueberstunden_frei_erlaubt_gleiche_zeiten():
    eintrag = Zeiteintrag(
        datum=date(2025, 1, 10),
        uhrzeit_von=time(12, 0),
        uhrzeit_bis=time(12, 0),
    )
    assert eintrag.uhrzeit_von == eintrag.uhrzeit_bis


def test_zeiteintrags_dto_unvollstaendig_ohne_validierungsfehler():
    dto = ZeiteintragsDTO(
        datum=date(2025, 1, 10),
        uhrzeit_von=time(8, 0),
        uhrzeit_bis=None,
    )
    assert dto.uhrzeit_bis is None


def test_urlaubsantrag_nur_halbe_tage():
    with pytest.raises(ValidationError, match="Halbtags"):
        Urlaubsantrag(
            datum_von=date(2025, 1, 1),
            datum_bis=date(2025, 1, 2),
            urlaubstyp="Erholung",
            urlaubstage=1.3,
        )


def test_krankmeldung_datum_von_nach_bis():
    with pytest.raises(ValidationError, match="krank_von"):
        Krankmeldung(
            krank_von=date(2025, 2, 10),
            krank_bis=date(2025, 2, 1),
            krankmeldungstage=1,
        )
