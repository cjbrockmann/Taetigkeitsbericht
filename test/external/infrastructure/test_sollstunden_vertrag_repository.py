from __future__ import annotations

from datetime import date

import pytest
from sqlmodel import Session, SQLModel, create_engine

from Core.Domain.models.models_worktime import SollstundenVertrag
from Core.Domain.services.sollstunden_vertrag_service import SollstundenVertragService
from External.Infrastructure.repositories.sollstunden_vertrag_sqlmodel_repository import (
    SqlSollstundenVertragRepository,
)
from External.Infrastructure.sqlmodel_tables import SollstundenVertragTable


@pytest.fixture
def session() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine, tables=[SollstundenVertragTable.__table__])
    with Session(engine) as s:
        yield s


def test_sollstunden_vertrag_speichern_und_gueltig_fuer_datum(session: Session) -> None:
    repo = SqlSollstundenVertragRepository(session)
    service = SollstundenVertragService(repo)
    vertrag = SollstundenVertrag(
        mandant_id=1,
        effective_date=date(2026, 1, 1),
        discontinued_date=date(2026, 12, 31),
        Montag=4.0,
        Dienstag=4.0,
        Mittwoch=4.0,
        Donnerstag=4.0,
        Freitag=0.0,
    )
    service.erfasse_sollstunden_vertrag(vertrag)
    gueltig = service.hole_gueltigen_vertrag_fuer_datum(1, date(2026, 6, 15))
    assert gueltig is not None
    assert gueltig.Montag == 4.0
    assert service.hole_gueltigen_vertrag_fuer_datum(1, date(2026, 12, 31)) is None


def test_sollstunden_vertrag_ueberlappende_zeitraeume(session: Session) -> None:
    repo = SqlSollstundenVertragRepository(session)
    service = SollstundenVertragService(repo)
    service.erfasse_sollstunden_vertrag(
        SollstundenVertrag(
            mandant_id=1,
            effective_date=date(2026, 1, 1),
            discontinued_date=date(2026, 6, 30),
        )
    )
    with pytest.raises(ValueError, match="ueberlappt"):
        service.erfasse_sollstunden_vertrag(
            SollstundenVertrag(
                mandant_id=1,
                effective_date=date(2026, 3, 1),
                discontinued_date=date(2026, 12, 31),
            )
        )


def test_sollstunden_vertrag_discontinued_nach_effective() -> None:
    with pytest.raises(ValueError, match="discontinued_date"):
        SollstundenVertrag(
            mandant_id=1,
            effective_date=date(2026, 6, 1),
            discontinued_date=date(2026, 1, 1),
        )
