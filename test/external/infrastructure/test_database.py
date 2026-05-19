from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, text

from External.Infrastructure.database import default_sqlite_database_url, init_db


def _mandant_id_spalte(conn, table: str) -> tuple[int, object] | None:
    for row in conn.execute(text(f"PRAGMA table_info({table})")).fetchall():
        if row[1] == "mandant_id":
            return row[3], row[4]
    return None


def _sqlite_default_ist_eins(dflt: object) -> bool:
    if dflt is None:
        return False
    return int(str(dflt).strip("'")) == 1


def _hat_mandant_id_index(conn, table: str) -> bool:
    rows = conn.execute(
        text(
            "SELECT name FROM sqlite_master "
            "WHERE type='index' AND tbl_name=:table AND name=:index_name"
        ),
        {"table": table, "index_name": f"ix_{table}_mandant_id"},
    ).fetchall()
    return len(rows) > 0


def test_migrate_fuegt_mandant_id_und_index_fuer_legacy_zeiteintrag_hinzu():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
    )
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE zeiteintrag (
                    id VARCHAR(36) PRIMARY KEY,
                    datum DATE NOT NULL,
                    uhrzeit_von TIME NOT NULL,
                    uhrzeit_bis TIME NOT NULL
                )
                """
            )
        )
    init_db(engine)
    with engine.connect() as conn:
        notnull, dflt = _mandant_id_spalte(conn, "zeiteintrag")
        assert notnull == 1
        assert _sqlite_default_ist_eins(dflt)
        assert _hat_mandant_id_index(conn, "zeiteintrag")


def test_migrate_mandant_id_idempotent():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
    )
    init_db(engine)
    init_db(engine)
    with engine.connect() as conn:
        for table in ("zeiteintrag", "stundenplan", "betriebsferien"):
            notnull, dflt = _mandant_id_spalte(conn, table)
            assert notnull == 1
            assert _sqlite_default_ist_eins(dflt)
            assert _hat_mandant_id_index(conn, table)


def test_default_sqlite_database_url_zeigt_auf_src_verzeichnis():
    database_url = default_sqlite_database_url()
    assert database_url.startswith("sqlite:///")

    database_path = Path(database_url.removeprefix("sqlite:///"))
    assert database_path.name == "taetigkeitsbericht.db"
    assert database_path.parent.name == "src"
