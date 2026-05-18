from __future__ import annotations

from pathlib import Path

from sqlalchemy import text
from sqlmodel import SQLModel, create_engine


def default_sqlite_database_url() -> str:
    src_root = Path(__file__).resolve().parents[2]
    database_path = src_root / "taetigkeitsbericht.db"
    return f"sqlite:///{database_path.as_posix()}"


def create_sqlite_engine(database_url: str | None = None):
    if database_url is None:
        database_url = default_sqlite_database_url()
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args)


def _migrate_krankmeldung_spalten_entfernen(engine) -> None:
    """Entfernt die Spalten krankmeldung und krankmeldungstagsname (Schema vor Mai 2026)."""
    if not str(engine.url).startswith("sqlite"):
        return
    with engine.begin() as conn:
        exists = conn.execute(
            text(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='krankmeldung' LIMIT 1"
            )
        ).fetchone()
        if exists is None:
            return
        cols = [
            row[1]
            for row in conn.execute(text("PRAGMA table_info(krankmeldung)")).fetchall()
        ]
        if "krankmeldung" in cols:
            conn.execute(text("ALTER TABLE krankmeldung DROP COLUMN krankmeldung"))
        if "krankmeldungstagsname" in cols:
            conn.execute(text("ALTER TABLE krankmeldung DROP COLUMN krankmeldungstagsname"))


def _migrate_feiertag_umfang_spalten(engine) -> None:
    if not str(engine.url).startswith("sqlite"):
        return
    with engine.begin() as conn:
        exists = conn.execute(
            text(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='feiertag' LIMIT 1"
            )
        ).fetchone()
        if exists is None:
            return
        cols = {
            row[1] for row in conn.execute(text("PRAGMA table_info(feiertag)")).fetchall()
        }
        if "ist_halber_tag" not in cols:
            conn.execute(
                text(
                    "ALTER TABLE feiertag ADD COLUMN ist_halber_tag "
                    "INTEGER NOT NULL DEFAULT 0"
                )
            )
        if "ist_offiziell" not in cols:
            conn.execute(
                text(
                    "ALTER TABLE feiertag ADD COLUMN ist_offiziell "
                    "INTEGER NOT NULL DEFAULT 1"
                )
            )


def init_db(engine) -> None:
    import External.Infrastructure.sqlmodel_tables  # noqa: F401 - Tabellen bei SQLModel registrieren

    SQLModel.metadata.create_all(engine)
    _migrate_krankmeldung_spalten_entfernen(engine)
    _migrate_feiertag_umfang_spalten(engine)
