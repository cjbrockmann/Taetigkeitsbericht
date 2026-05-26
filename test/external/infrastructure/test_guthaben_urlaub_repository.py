from __future__ import annotations

from datetime import date

import pytest
from sqlmodel import Session, SQLModel, create_engine

from Core.Domain.models.models_worktime import GuthabenUrlaub
from Core.Domain.services.guthaben_urlaub_service import GuthabenUrlaubService
from External.Infrastructure.repositories.guthaben_urlaub_sqlmodel_repository import (
    SqlGuthabenUrlaubRepository,
)
from External.Infrastructure.sqlmodel_tables import GuthabenUrlaubTable


@pytest.fixture
def session() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine, tables=[GuthabenUrlaubTable.__table__])
    with Session(engine) as s:
        yield s


def test_guthaben_urlaub_speichern_und_laden(session: Session) -> None:
    repo = SqlGuthabenUrlaubRepository(session)
    service = GuthabenUrlaubService(repo)
    eintrag = GuthabenUrlaub(
        mandant_id=1,
        datum=date(2026, 3, 1),
        urlaubstage_guthaben_vorjahr=5.0,
        urlaubstage_guthaben_vormonat=4.0,
        urlaubstage_im_monat_aktuell=1.0,
    )
    gespeichert = service.erfasse_guthaben_urlaub(eintrag)
    assert gespeichert.id is not None
    geladen = service.hole_guthaben_urlaub_fuer_monat(1, date(2026, 3, 1))
    assert geladen is not None
    assert geladen.urlaubstage_guthaben_vorjahr == 5.0


def test_guthaben_urlaub_doppelter_monat(session: Session) -> None:
    repo = SqlGuthabenUrlaubRepository(session)
    service = GuthabenUrlaubService(repo)
    datum = date(2026, 4, 1)
    service.erfasse_guthaben_urlaub(GuthabenUrlaub(mandant_id=1, datum=datum))
    with pytest.raises(ValueError, match="existiert bereits"):
        service.erfasse_guthaben_urlaub(GuthabenUrlaub(mandant_id=1, datum=datum))


def test_guthaben_urlaub_datum_muss_erster_sein() -> None:
    with pytest.raises(ValueError, match="1. eines Monats"):
        GuthabenUrlaub(mandant_id=1, datum=date(2026, 4, 15))
