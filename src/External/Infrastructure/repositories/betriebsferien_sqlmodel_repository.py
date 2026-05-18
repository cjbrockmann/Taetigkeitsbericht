from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy import and_
from sqlmodel import Session, select

from Core.Domain.models.models_worktime import Betriebsferien
from External.Infrastructure.sqlmodel_tables import BetriebsferienTable


def _row_to_domain(row: BetriebsferienTable) -> Betriebsferien:
    return Betriebsferien(
        id=row.id,
        mandant_id=row.mandant_id,
        datum_von=row.datum_von,
        datum_bis=row.datum_bis,
        betriebsferienname=row.betriebsferienname,
        anmerkung=row.anmerkung,
    )


class SqlBetriebsferienRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, eintrag: Betriebsferien) -> Betriebsferien:
        if eintrag.mandant_id is None:
            raise ValueError("mandant_id ist fuer Betriebsferien erforderlich.")
        row: BetriebsferienTable | None = None
        if eintrag.id is not None:
            row = self._session.get(BetriebsferienTable, eintrag.id)
        if row is None:
            row = BetriebsferienTable(
                id=eintrag.id,
                mandant_id=eintrag.mandant_id,
                datum_von=eintrag.datum_von,
                datum_bis=eintrag.datum_bis,
                betriebsferienname=eintrag.betriebsferienname,
                anmerkung=eintrag.anmerkung,
            )
            self._session.add(row)
        else:
            if row.mandant_id != eintrag.mandant_id:
                raise ValueError("Betriebsferien gehoeren zu einem anderen Mandanten.")
            row.datum_von = eintrag.datum_von
            row.datum_bis = eintrag.datum_bis
            row.betriebsferienname = eintrag.betriebsferienname
            row.anmerkung = eintrag.anmerkung
        self._session.commit()
        self._session.refresh(row)
        return _row_to_domain(row)

    def get_by_id(self, mandant_id: int, eintrag_id: int) -> Optional[Betriebsferien]:
        row = self._session.get(BetriebsferienTable, eintrag_id)
        if row is None or row.mandant_id != mandant_id:
            return None
        return _row_to_domain(row)

    def list_all(self, mandant_id: int, jahr: Optional[int] = None) -> list[Betriebsferien]:
        stmt = (
            select(BetriebsferienTable)
            .where(BetriebsferienTable.mandant_id == mandant_id)
            .order_by(BetriebsferienTable.datum_von, BetriebsferienTable.id)
        )
        if jahr is not None:
            jahresanfang = date(jahr, 1, 1)
            jahresende = date(jahr, 12, 31)
            stmt = stmt.where(
                and_(
                    BetriebsferienTable.datum_von <= jahresende,
                    BetriebsferienTable.datum_bis >= jahresanfang,
                )
            )
        rows = list(self._session.exec(stmt).all())
        return [_row_to_domain(r) for r in rows]

    def delete_by_id(self, mandant_id: int, eintrag_id: int) -> bool:
        row = self._session.get(BetriebsferienTable, eintrag_id)
        if row is None or row.mandant_id != mandant_id:
            return False
        self._session.delete(row)
        self._session.commit()
        return True
