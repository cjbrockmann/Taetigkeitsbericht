from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy import extract
from sqlmodel import Session, select

from Core.Domain.models.models_worktime import Feiertag
from External.Infrastructure.sqlmodel_tables import FeiertagTable


def _row_to_domain(row: FeiertagTable) -> Feiertag:
    return Feiertag(
        datum=row.datum,
        feiertagsname=row.feiertagsname,
        hinweis=row.hinweis,
        ist_halber_tag=row.ist_halber_tag,
        ist_offiziell=row.ist_offiziell,
    )


class SqlFeiertagRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, eintrag: Feiertag) -> Feiertag:
        row = FeiertagTable(
            datum=eintrag.datum,
            feiertagsname=eintrag.feiertagsname,
            hinweis=eintrag.hinweis,
            ist_halber_tag=eintrag.ist_halber_tag,
            ist_offiziell=eintrag.ist_offiziell,
        )
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)
        return _row_to_domain(row)

    def update(self, eintrag: Feiertag) -> bool:
        row = self._session.get(FeiertagTable, eintrag.datum)
        if row is None:
            return False
        row.feiertagsname = eintrag.feiertagsname
        row.hinweis = eintrag.hinweis
        row.ist_halber_tag = eintrag.ist_halber_tag
        row.ist_offiziell = eintrag.ist_offiziell
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)
        return True

    def get_by_datum(self, datum: date) -> list[Feiertag]:
        stmt = select(FeiertagTable).where(FeiertagTable.datum == datum)
        rows = list(self._session.exec(stmt).all())
        return [_row_to_domain(r) for r in rows]

    def list_all(self, jahr: Optional[int] = None) -> list[Feiertag]:
        stmt = select(FeiertagTable).order_by(FeiertagTable.datum)
        if jahr is not None:
            stmt = stmt.where(extract("year", FeiertagTable.datum) == jahr)
        rows = list(self._session.exec(stmt).all())
        return [_row_to_domain(r) for r in rows]

    def delete_by_datum(self, datum: date) -> bool:
        rows = list(self._session.exec(select(FeiertagTable).where(FeiertagTable.datum == datum)).all())
        for row in rows:
            self._session.delete(row)
        self._session.commit()
        return len(rows) > 0
