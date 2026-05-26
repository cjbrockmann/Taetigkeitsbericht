from __future__ import annotations

from datetime import date

import pytest
from sqlmodel import Session, SQLModel, create_engine

from Core.Domain.models.models_worktime import GuthabenStunden
from Core.Domain.services.guthaben_stunden_service import GuthabenStundenService
from External.Infrastructure.repositories.guthaben_stunden_sqlmodel_repository import (
    SqlGuthabenStundenRepository,
)
from External.Infrastructure.sqlmodel_tables import GuthabenStundenTable


@pytest.fixture
def session() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine, tables=[GuthabenStundenTable.__table__])
    with Session(engine) as s:
        yield s


def test_guthaben_stunden_speichern_und_laden(session: Session) -> None:
    repo = SqlGuthabenStundenRepository(session)
    service = GuthabenStundenService(repo)
    eintrag = GuthabenStunden(
        mandant_id=1,
        datum=date(2026, 3, 1),
        stunden_guthaben_vormonat=8.0,
        stunden_guthaben_vormonat_manuell=7.5,
        stunden_guthaben_monatsende_aktuell=10.5,
    )
    gespeichert = service.erfasse_guthaben_stunden(eintrag)
    assert gespeichert.id is not None
    assert gespeichert.stunden_guthaben_vormonat_manuell == 7.5
    geladen = service.hole_guthaben_stunden_fuer_monat(1, date(2026, 3, 1))
    assert geladen is not None
    assert geladen.stunden_guthaben_vormonat_manuell == 7.5
    assert geladen.stunden_guthaben_monatsende_aktuell == 10.5


def test_guthaben_stunden_vormonat_manuell_update(session: Session) -> None:
    repo = SqlGuthabenStundenRepository(session)
    service = GuthabenStundenService(repo)
    datum = date(2026, 5, 1)
    gespeichert = service.erfasse_guthaben_stunden(
        GuthabenStunden(mandant_id=1, datum=datum, stunden_guthaben_vormonat_manuell=3.0)
    )
    aktualisiert = service.erfasse_guthaben_stunden(
        gespeichert.model_copy(
            update={"stunden_guthaben_vormonat_manuell": None, "stunden_guthaben_vormonat": 4.0}
        )
    )
    assert aktualisiert.stunden_guthaben_vormonat_manuell is None
    assert aktualisiert.stunden_guthaben_vormonat == 4.0


def test_guthaben_stunden_doppelter_monat(session: Session) -> None:
    repo = SqlGuthabenStundenRepository(session)
    service = GuthabenStundenService(repo)
    datum = date(2026, 4, 1)
    service.erfasse_guthaben_stunden(GuthabenStunden(mandant_id=1, datum=datum))
    with pytest.raises(ValueError, match="existiert bereits"):
        service.erfasse_guthaben_stunden(GuthabenStunden(mandant_id=1, datum=datum))


def test_guthaben_stunden_manuell_leerstring_wird_null(session: Session) -> None:
    from sqlalchemy import text

    session.execute(
        text(
            "INSERT INTO guthaben_stunden "
            "(mandant_id, datum, stunden_guthaben_vormonat, "
            "stunden_guthaben_vormonat_manuell, stunden_guthaben_monatsende_aktuell) "
            "VALUES (1, '2026-05-01', 0, '', 0)"
        )
    )
    session.commit()
    repo = SqlGuthabenStundenRepository(session)
    geladen = repo.get_by_mandant_und_datum(1, date(2026, 5, 1))
    assert geladen is not None
    assert geladen.stunden_guthaben_vormonat_manuell is None


def test_guthaben_stunden_datum_muss_erster_sein() -> None:
    with pytest.raises(ValueError, match="1. eines Monats"):
        GuthabenStunden(mandant_id=1, datum=date(2026, 4, 15))
