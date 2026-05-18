from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel

from External.Infrastructure import sqlmodel_tables  # noqa: F401 — Tabellen registrieren


@pytest.fixture
def sqlite_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(sqlite_engine) -> Iterator[Session]:
    with Session(sqlite_engine) as session:
        yield session
