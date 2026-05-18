from __future__ import annotations

from datetime import date

from Core.Domain.models.models_worktime import Feiertag
from Core.Domain.services.feiertag_service import FeiertagService
from External.Infrastructure.repositories.feiertag_sqlmodel_repository import (
    SqlFeiertagRepository,
)


def test_feiertag_service_mit_sqlmodel_repository(db_session):
    repo = SqlFeiertagRepository(db_session)
    service = FeiertagService(repo)
    tag = date(2025, 12, 25)
    service.erfasse_feiertag(Feiertag(datum=tag, feiertagsname="Weihnachten"))
    liste = service.liste_feiertage(2025)
    assert len(liste) == 1
    assert liste[0].feiertagsname == "Weihnachten"
    assert service.loesche_feiertag(tag) is True
