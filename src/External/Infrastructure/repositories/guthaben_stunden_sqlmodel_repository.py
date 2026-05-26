from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy import extract
from sqlmodel import Session, select

from Core.Domain.models.models_worktime import GuthabenStunden
from External.Infrastructure.sqlmodel_tables import GuthabenStundenTable


def _optional_float_from_db(wert: object) -> float | None:
    """SQLite kann leere Strings statt NULL liefern."""
    if wert is None:
        return None
    if isinstance(wert, str):
        text = wert.strip()
        if not text:
            return None
        return float(text)
    return float(wert)


def _row_to_domain(row: GuthabenStundenTable) -> GuthabenStunden:
    return GuthabenStunden(
        id=row.id,
        mandant_id=row.mandant_id,
        datum=row.datum,
        stunden_guthaben_vormonat=float(row.stunden_guthaben_vormonat or 0),
        stunden_guthaben_vormonat_manuell=_optional_float_from_db(
            row.stunden_guthaben_vormonat_manuell
        ),
        stunden_guthaben_monatsende_aktuell=float(row.stunden_guthaben_monatsende_aktuell or 0),
    )


class SqlGuthabenStundenRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, eintrag: GuthabenStunden) -> GuthabenStunden:
        if eintrag.mandant_id is None:
            raise ValueError("mandant_id ist fuer GuthabenStunden erforderlich.")
        row: GuthabenStundenTable | None = None
        if eintrag.id is not None:
            row = self._session.get(GuthabenStundenTable, eintrag.id)
        if row is None:
            row = self._session.exec(
                select(GuthabenStundenTable)
                .where(GuthabenStundenTable.mandant_id == eintrag.mandant_id)
                .where(GuthabenStundenTable.datum == eintrag.datum)
            ).first()
        if row is None:
            row = GuthabenStundenTable(
                id=eintrag.id,
                mandant_id=eintrag.mandant_id,
                datum=eintrag.datum,
                stunden_guthaben_vormonat=eintrag.stunden_guthaben_vormonat,
                stunden_guthaben_vormonat_manuell=eintrag.stunden_guthaben_vormonat_manuell,
                stunden_guthaben_monatsende_aktuell=eintrag.stunden_guthaben_monatsende_aktuell,
            )
            self._session.add(row)
        else:
            if row.mandant_id != eintrag.mandant_id:
                raise ValueError("GuthabenStunden gehoert zu einem anderen Mandanten.")
            row.datum = eintrag.datum
            row.stunden_guthaben_vormonat = eintrag.stunden_guthaben_vormonat
            row.stunden_guthaben_vormonat_manuell = eintrag.stunden_guthaben_vormonat_manuell
            row.stunden_guthaben_monatsende_aktuell = (
                eintrag.stunden_guthaben_monatsende_aktuell
            )
        self._session.commit()
        self._session.refresh(row)
        return _row_to_domain(row)

    def get_by_id(self, mandant_id: int, eintrag_id: int) -> Optional[GuthabenStunden]:
        row = self._session.get(GuthabenStundenTable, eintrag_id)
        if row is None or row.mandant_id != mandant_id:
            return None
        return _row_to_domain(row)

    def get_by_mandant_und_datum(
        self, mandant_id: int, datum: date
    ) -> Optional[GuthabenStunden]:
        stmt = (
            select(GuthabenStundenTable)
            .where(GuthabenStundenTable.mandant_id == mandant_id)
            .where(GuthabenStundenTable.datum == datum)
        )
        row = self._session.exec(stmt).first()
        if row is None:
            return None
        return _row_to_domain(row)

    def list_all(self, mandant_id: int, jahr: Optional[int] = None) -> list[GuthabenStunden]:
        stmt = (
            select(GuthabenStundenTable)
            .where(GuthabenStundenTable.mandant_id == mandant_id)
            .order_by(GuthabenStundenTable.datum, GuthabenStundenTable.id)
        )
        if jahr is not None:
            stmt = stmt.where(extract("year", GuthabenStundenTable.datum) == jahr)
        rows = list(self._session.exec(stmt).all())
        return [_row_to_domain(r) for r in rows]

    def delete_by_id(self, mandant_id: int, eintrag_id: int) -> bool:
        row = self._session.get(GuthabenStundenTable, eintrag_id)
        if row is None or row.mandant_id != mandant_id:
            return False
        self._session.delete(row)
        self._session.commit()
        return True
