from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy import or_
from sqlmodel import Session, select

from Core.Domain.models.models_worktime import SollstundenVertrag
from External.Infrastructure.sqlmodel_tables import SollstundenVertragTable


def _row_to_domain(row: SollstundenVertragTable) -> SollstundenVertrag:
    return SollstundenVertrag(
        id=row.id,
        mandant_id=row.mandant_id,
        effective_date=row.effective_date,
        discontinued_date=row.discontinued_date,
        Montag=row.Montag,
        Dienstag=row.Dienstag,
        Mittwoch=row.Mittwoch,
        Donnerstag=row.Donnerstag,
        Freitag=row.Freitag,
        Samstag=row.Samstag,
        Sonntag=row.Sonntag,
    )


class SqlSollstundenVertragRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, vertrag: SollstundenVertrag) -> SollstundenVertrag:
        if vertrag.mandant_id is None:
            raise ValueError("mandant_id ist fuer SollstundenVertrag erforderlich.")
        row: SollstundenVertragTable | None = None
        if vertrag.id is not None:
            row = self._session.get(SollstundenVertragTable, vertrag.id)
        if row is None:
            row = SollstundenVertragTable(
                id=vertrag.id,
                mandant_id=vertrag.mandant_id,
                effective_date=vertrag.effective_date,
                discontinued_date=vertrag.discontinued_date,
                Montag=vertrag.Montag,
                Dienstag=vertrag.Dienstag,
                Mittwoch=vertrag.Mittwoch,
                Donnerstag=vertrag.Donnerstag,
                Freitag=vertrag.Freitag,
                Samstag=vertrag.Samstag,
                Sonntag=vertrag.Sonntag,
            )
            self._session.add(row)
        else:
            if row.mandant_id != vertrag.mandant_id:
                raise ValueError("SollstundenVertrag gehoert zu einem anderen Mandanten.")
            row.effective_date = vertrag.effective_date
            row.discontinued_date = vertrag.discontinued_date
            row.Montag = vertrag.Montag
            row.Dienstag = vertrag.Dienstag
            row.Mittwoch = vertrag.Mittwoch
            row.Donnerstag = vertrag.Donnerstag
            row.Freitag = vertrag.Freitag
            row.Samstag = vertrag.Samstag
            row.Sonntag = vertrag.Sonntag
        self._session.commit()
        self._session.refresh(row)
        return _row_to_domain(row)

    def get_by_id(self, mandant_id: int, vertrag_id: int) -> Optional[SollstundenVertrag]:
        row = self._session.get(SollstundenVertragTable, vertrag_id)
        if row is None or row.mandant_id != mandant_id:
            return None
        return _row_to_domain(row)

    def list_all(self, mandant_id: int) -> list[SollstundenVertrag]:
        stmt = (
            select(SollstundenVertragTable)
            .where(SollstundenVertragTable.mandant_id == mandant_id)
            .order_by(SollstundenVertragTable.effective_date, SollstundenVertragTable.id)
        )
        rows = list(self._session.exec(stmt).all())
        return [_row_to_domain(r) for r in rows]

    def get_gueltig_fuer_datum(
        self, mandant_id: int, datum: date
    ) -> Optional[SollstundenVertrag]:
        stmt = (
            select(SollstundenVertragTable)
            .where(SollstundenVertragTable.mandant_id == mandant_id)
            .where(SollstundenVertragTable.effective_date <= datum)
            .where(
                or_(
                    SollstundenVertragTable.discontinued_date.is_(None),
                    SollstundenVertragTable.discontinued_date > datum,
                )
            )
            .order_by(SollstundenVertragTable.effective_date.desc())
        )
        row = self._session.exec(stmt).first()
        if row is None:
            return None
        return _row_to_domain(row)

    def delete_by_id(self, mandant_id: int, vertrag_id: int) -> bool:
        row = self._session.get(SollstundenVertragTable, vertrag_id)
        if row is None or row.mandant_id != mandant_id:
            return False
        self._session.delete(row)
        self._session.commit()
        return True

    def hat_eintraege(self) -> bool:
        row = self._session.exec(select(SollstundenVertragTable).limit(1)).first()
        return row is not None
