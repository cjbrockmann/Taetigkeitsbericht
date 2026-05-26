from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from sqlmodel import Session, SQLModel, create_engine

from App.app_config import (
    SOLLSTUNDEN_VERTRAG_BACKUP_TOML,
    SOLLSTUNDEN_VERTRAG_TOML,
)
from App.sollstunden_vertrag_sync import (
    SOLLSTUNDEN_VERTRAG_PLATZHALTER,
    importiere_sollstunden_vertraege_beim_erststart,
)
from Core.Application.sollstunden_vertrag_anwendung import SollstundenVertragAnwendung
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


def test_erstimport_benennt_toml_in_backup_um(tmp_path: Path, session: Session) -> None:
    quelle = tmp_path / SOLLSTUNDEN_VERTRAG_TOML
    quelle.write_text(
        """
[[sollstunden_vertrag.vertrag]]
mandant_id = 1
effective_date = "2026-01-01"
wochenstunden = [
    { wochentag = 1, stunden = "4:00", name = "Montag" },
    { wochentag = 2, stunden = "0:00", name = "Dienstag" },
    { wochentag = 3, stunden = "0:00", name = "Mittwoch" },
    { wochentag = 4, stunden = "0:00", name = "Donnerstag" },
    { wochentag = 5, stunden = "0:00", name = "Freitag" },
    { wochentag = 6, stunden = "0:00", name = "Samstag" },
    { wochentag = 7, stunden = "0:00", name = "Sonntag" },
]
""",
        encoding="utf-8",
    )
    anwendung = SollstundenVertragAnwendung(
        SollstundenVertragService(SqlSollstundenVertragRepository(session))
    )

    inhalt_vor_import = quelle.read_text(encoding="utf-8")
    assert (
        importiere_sollstunden_vertraege_beim_erststart(
            tmp_path, anwendung, backup_erstellen=True
        )
        is True
    )
    assert quelle.is_file()
    assert quelle.read_text(encoding="utf-8") == SOLLSTUNDEN_VERTRAG_PLATZHALTER
    assert (tmp_path / SOLLSTUNDEN_VERTRAG_BACKUP_TOML).is_file()
    assert (
        tmp_path / SOLLSTUNDEN_VERTRAG_BACKUP_TOML
    ).read_text(encoding="utf-8") == inhalt_vor_import

    vertrag = anwendung.hole_gueltig_fuer_datum(1, date(2026, 3, 2))
    assert vertrag is not None
    assert vertrag.Montag == 4.0

    assert (
        importiere_sollstunden_vertraege_beim_erststart(
            tmp_path, anwendung, backup_erstellen=True
        )
        is False
    )


def test_erstimport_laesst_toml_unberührt_ohne_backup(
    tmp_path: Path, session: Session
) -> None:
    quelle = tmp_path / SOLLSTUNDEN_VERTRAG_TOML
    inhalt = """
[[sollstunden_vertrag.vertrag]]
mandant_id = 1
effective_date = "2026-01-01"
wochenstunden = [{ wochentag = 1, stunden = "4:00", name = "Montag" }]
"""
    quelle.write_text(inhalt, encoding="utf-8")
    anwendung = SollstundenVertragAnwendung(
        SollstundenVertragService(SqlSollstundenVertragRepository(session))
    )

    assert (
        importiere_sollstunden_vertraege_beim_erststart(
            tmp_path, anwendung, backup_erstellen=False
        )
        is True
    )
    assert quelle.read_text(encoding="utf-8") == inhalt
    assert not (tmp_path / SOLLSTUNDEN_VERTRAG_BACKUP_TOML).is_file()


def test_kein_import_wenn_tabelle_bereits_vertraege_hat(
    tmp_path: Path, session: Session
) -> None:
    quelle = tmp_path / SOLLSTUNDEN_VERTRAG_TOML
    quelle.write_text(
        """
[[sollstunden_vertrag.vertrag]]
mandant_id = 1
effective_date = "2026-01-01"
wochenstunden = [{ wochentag = 1, stunden = "8:00", name = "Mo" }]
""",
        encoding="utf-8",
    )
    anwendung = SollstundenVertragAnwendung(
        SollstundenVertragService(SqlSollstundenVertragRepository(session))
    )
    anwendung.erfasse(
        SollstundenVertrag(
            mandant_id=1,
            effective_date=date(2025, 1, 1),
            Montag=8.0,
        )
    )
    inhalt_vorher = quelle.read_text(encoding="utf-8")

    assert (
        importiere_sollstunden_vertraege_beim_erststart(
            tmp_path, anwendung, backup_erstellen=False
        )
        is False
    )
    assert quelle.read_text(encoding="utf-8") == inhalt_vorher
    assert not (tmp_path / SOLLSTUNDEN_VERTRAG_BACKUP_TOML).is_file()
    assert len(anwendung.liste(1)) == 1
