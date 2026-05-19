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


_MANDANT_ID_TABELLEN = ("zeiteintrag", "stundenplan", "betriebsferien")


def _sqlite_table_exists(conn, table_name: str) -> bool:
    row = conn.execute(
        text(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=:name LIMIT 1"
        ),
        {"name": table_name},
    ).fetchone()
    return row is not None


def _sqlite_table_column_info(conn, table_name: str) -> dict[str, tuple[int, object]]:
    """Spaltenname -> (notnull, dflt_value) aus PRAGMA table_info."""
    rows = conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
    return {row[1]: (row[3], row[4]) for row in rows}


def _migrate_mandant_id_spalten_und_indizes(engine) -> None:
    """mandant_id NOT NULL DEFAULT 1 und Index auf zeiteintrag, stundenplan, betriebsferien."""
    if not str(engine.url).startswith("sqlite"):
        return
    with engine.begin() as conn:
        for table in _MANDANT_ID_TABELLEN:
            if not _sqlite_table_exists(conn, table):
                continue
            cols = _sqlite_table_column_info(conn, table)
            if "mandant_id" not in cols:
                conn.execute(
                    text(
                        f"ALTER TABLE {table} ADD COLUMN mandant_id "
                        "INTEGER NOT NULL DEFAULT 1"
                    )
                )
            else:
                conn.execute(
                    text(f"UPDATE {table} SET mandant_id = 1 WHERE mandant_id IS NULL")
                )
            conn.execute(
                text(
                    f"CREATE INDEX IF NOT EXISTS ix_{table}_mandant_id "
                    f"ON {table} (mandant_id)"
                )
            )


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
    _migrate_mandant_id_spalten_und_indizes(engine)
