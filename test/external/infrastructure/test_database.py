from __future__ import annotations

from pathlib import Path

from External.Infrastructure.database import default_sqlite_database_url


def test_default_sqlite_database_url_zeigt_auf_src_verzeichnis():
    database_url = default_sqlite_database_url()
    assert database_url.startswith("sqlite:///")

    database_path = Path(database_url.removeprefix("sqlite:///"))
    assert database_path.name == "taetigkeitsbericht.db"
    assert database_path.parent.name == "src"
