from __future__ import annotations

from datetime import date
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import extract
from sqlmodel import Session, select

from Core.Domain.models.models_worktime import Zeiteintrag
from External.Infrastructure.sqlmodel_tables import ZeiteintragTable


def _row_to_domain(row: ZeiteintragTable) -> Zeiteintrag:
    return Zeiteintrag(
        id=UUID(row.id),
        mandant_id=row.mandant_id,
        datum=row.datum,
        uhrzeit_von=row.uhrzeit_von,
        uhrzeit_bis=row.uhrzeit_bis,
        pause_beginn=row.pause_beginn,
        pause_ende=row.pause_ende,
        pause2_beginn=row.pause2_beginn,
        pause2_ende=row.pause2_ende,
        anmerkung=row.anmerkung,
    )


class SqlZeiteintragRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, eintrag: Zeiteintrag) -> Zeiteintrag:
        if eintrag.mandant_id is None:
            raise ValueError("mandant_id ist fuer Zeiteintrag erforderlich.")
        row_id = str(eintrag.id or uuid4())
        row = self._session.get(ZeiteintragTable, row_id)
        if row is None:
            row = ZeiteintragTable(
                id=row_id,
                mandant_id=eintrag.mandant_id,
                datum=eintrag.datum,
                uhrzeit_von=eintrag.uhrzeit_von,
                uhrzeit_bis=eintrag.uhrzeit_bis,
                pause_beginn=eintrag.pause_beginn,
                pause_ende=eintrag.pause_ende,
                pause2_beginn=eintrag.pause2_beginn,
                pause2_ende=eintrag.pause2_ende,
                anmerkung=eintrag.anmerkung,
            )
            self._session.add(row)
        else:
            if row.mandant_id != eintrag.mandant_id:
                raise ValueError("Zeiteintrag gehoert zu einem anderen Mandanten.")
            row.datum = eintrag.datum
            row.uhrzeit_von = eintrag.uhrzeit_von
            row.uhrzeit_bis = eintrag.uhrzeit_bis
            row.pause_beginn = eintrag.pause_beginn
            row.pause_ende = eintrag.pause_ende
            row.pause2_beginn = eintrag.pause2_beginn
            row.pause2_ende = eintrag.pause2_ende
            row.anmerkung = eintrag.anmerkung
        self._session.commit()
        self._session.refresh(row)
        return _row_to_domain(row)

    def get_by_datum(self, mandant_id: int, datum: date) -> list[Zeiteintrag]:
        stmt = (
            select(ZeiteintragTable)
            .where(ZeiteintragTable.mandant_id == mandant_id)
            .where(ZeiteintragTable.datum == datum)
            .order_by(ZeiteintragTable.uhrzeit_von)
        )
        rows = list(self._session.exec(stmt).all())
        return [_row_to_domain(r) for r in rows]

    def list_all(
        self,
        mandant_id: int,
        jahr: Optional[int] = None,
        monat: Optional[int] = None,
    ) -> list[Zeiteintrag]:
        stmt = (
            select(ZeiteintragTable)
            .where(ZeiteintragTable.mandant_id == mandant_id)
            .order_by(ZeiteintragTable.datum, ZeiteintragTable.uhrzeit_von)
        )
        if jahr is not None and monat is not None:
            stmt = stmt.where(extract("year", ZeiteintragTable.datum) == jahr).where(
                extract("month", ZeiteintragTable.datum) == monat
            )
        elif jahr is not None:
            stmt = stmt.where(extract("year", ZeiteintragTable.datum) == jahr)
        rows = list(self._session.exec(stmt).all())
        return [_row_to_domain(r) for r in rows]

    def delete_by_datum(self, mandant_id: int, datum: date) -> bool:
        rows = list(
            self._session.exec(
                select(ZeiteintragTable)
                .where(ZeiteintragTable.mandant_id == mandant_id)
                .where(ZeiteintragTable.datum == datum)
            ).all()
        )
        for row in rows:
            self._session.delete(row)
        self._session.commit()
        return len(rows) > 0

    def delete_by_id(self, mandant_id: int, eintrag_id: UUID) -> bool:
        row = self._session.get(ZeiteintragTable, str(eintrag_id))
        if row is None or row.mandant_id != mandant_id:
            return False
        self._session.delete(row)
        self._session.commit()
        return True
