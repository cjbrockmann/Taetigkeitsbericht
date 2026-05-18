from __future__ import annotations

from datetime import date, time
from uuid import uuid4

from Core.Domain.models.models_worktime import Zeiteintrag
from External.Infrastructure.repositories.zeiteintrag_sqlmodel_repository import (
    SqlZeiteintragRepository,
)


def test_save_und_get_by_datum(db_session):
    repo = SqlZeiteintragRepository(db_session)
    eintrag = Zeiteintrag(
        id=uuid4(),
        mandant_id=1,
        datum=date(2025, 5, 12),
        uhrzeit_von=time(9, 0),
        uhrzeit_bis=time(17, 0),
        anmerkung="Test",
    )
    repo.save(eintrag)
    geladen = repo.get_by_datum(1, date(2025, 5, 12))
    assert len(geladen) == 1
    assert geladen[0].anmerkung == "Test"


def test_list_all_nach_jahr_und_monat(db_session):
    repo = SqlZeiteintragRepository(db_session)
    repo.save(
        Zeiteintrag(
            mandant_id=1,
            datum=date(2025, 3, 1),
            uhrzeit_von=time(8, 0),
            uhrzeit_bis=time(12, 0),
        )
    )
    repo.save(
        Zeiteintrag(
            mandant_id=1,
            datum=date(2025, 4, 1),
            uhrzeit_von=time(8, 0),
            uhrzeit_bis=time(12, 0),
        )
    )
    maerz = repo.list_all(1, jahr=2025, monat=3)
    assert len(maerz) == 1
    assert maerz[0].datum.month == 3


def test_delete_by_id(db_session):
    repo = SqlZeiteintragRepository(db_session)
    eid = uuid4()
    repo.save(
        Zeiteintrag(
            id=eid,
            mandant_id=1,
            datum=date(2025, 6, 1),
            uhrzeit_von=time(8, 0),
            uhrzeit_bis=time(9, 0),
        )
    )
    assert repo.delete_by_id(1, eid) is True
    assert repo.get_by_datum(1, date(2025, 6, 1)) == []
