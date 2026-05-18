from __future__ import annotations

from datetime import date, time
from uuid import uuid4

from Core.Domain.models.models_worktime import (
    Feiertag,
    Krankmeldung,
    Stundenplan,
    Urlaubsantrag,
    Zeiteintrag,
    ZeiteintragsDTO,
)


def zeiteintrag(
    *,
    mandant_id: int = 1,
    datum: date | None = None,
    uhrzeit_von: time | None = time(8, 0),
    uhrzeit_bis: time | None = time(16, 0),
    anmerkung: str | None = None,
) -> Zeiteintrag:
    return Zeiteintrag(
        id=uuid4(),
        mandant_id=mandant_id,
        datum=datum or date(2025, 3, 10),
        uhrzeit_von=uhrzeit_von,
        uhrzeit_bis=uhrzeit_bis,
        anmerkung=anmerkung,
    )


def zeiteintrags_dto(
    *,
    mandant_id: int = 1,
    datum: date | None = None,
    uhrzeit_von: time | None = None,
    uhrzeit_bis: time | None = None,
    anmerkung: str | None = None,
) -> ZeiteintragsDTO:
    return ZeiteintragsDTO(
        id=None,
        mandant_id=mandant_id,
        datum=datum or date(2025, 3, 10),
        uhrzeit_von=uhrzeit_von,
        uhrzeit_bis=uhrzeit_bis,
        anmerkung=anmerkung,
    )


def stundenplan_montag(
    *,
    mandant_id: int = 1,
    von: time = time(8, 0),
    bis: time = time(12, 0),
) -> Stundenplan:
    return Stundenplan(
        id=1,
        mandant_id=mandant_id,
        wochentag=1,
        uhrzeit_von=von,
        uhrzeit_bis=bis,
    )


def feiertag(datum: date, name: str = "Feiertag") -> Feiertag:
    return Feiertag(datum=datum, feiertagsname=name)


def urlaub(von: date, bis: date) -> Urlaubsantrag:
    return Urlaubsantrag(
        id=1,
        datum_von=von,
        datum_bis=bis,
        urlaubstyp="Erholung",
        urlaubstage=1.0,
        genehmigt=True,
    )


def krank(von: date, bis: date) -> Krankmeldung:
    return Krankmeldung(
        id=1,
        krank_von=von,
        krank_bis=bis,
        krankmeldungstage=1,
    )
