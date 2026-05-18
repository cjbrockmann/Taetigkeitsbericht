from __future__ import annotations

from sqlmodel import Session, select

from Core.Domain.models.models_worktime import Stundenplan
from External.Infrastructure.sqlmodel_tables import StundenplanTable


def _row_to_domain(row: StundenplanTable) -> Stundenplan:
    return Stundenplan(
        id=row.id,
        mandant_id=row.mandant_id,
        wochentag=row.wochentag,
        uhrzeit_von=row.uhrzeit_von,
        uhrzeit_bis=row.uhrzeit_bis,
        pause_beginn=row.pause_beginn,
        pause_ende=row.pause_ende,
        pause2_beginn=row.pause2_beginn,
        pause2_ende=row.pause2_ende,
        anmerkung=row.anmerkung,
    )


class SqlStundenplanRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, eintrag: Stundenplan) -> Stundenplan:
        if eintrag.mandant_id is None:
            raise ValueError("mandant_id ist fuer Stundenplan erforderlich.")
        row: StundenplanTable | None = None
        if eintrag.id is not None:
            row = self._session.get(StundenplanTable, eintrag.id)
        if row is None:
            row = StundenplanTable(
                id=eintrag.id,
                mandant_id=eintrag.mandant_id,
                wochentag=eintrag.wochentag,
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
                raise ValueError("Stundenplaneintrag gehoert zu einem anderen Mandanten.")
            row.wochentag = eintrag.wochentag
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

    def get_by_wochentag(self, mandant_id: int, wochentag: int) -> list[Stundenplan]:
        stmt = (
            select(StundenplanTable)
            .where(StundenplanTable.mandant_id == mandant_id)
            .where(StundenplanTable.wochentag == wochentag)
            .order_by(StundenplanTable.uhrzeit_von)
        )
        rows = list(self._session.exec(stmt).all())
        return [_row_to_domain(r) for r in rows]

    def list_all(self, mandant_id: int) -> list[Stundenplan]:
        stmt = (
            select(StundenplanTable)
            .where(StundenplanTable.mandant_id == mandant_id)
            .order_by(
                StundenplanTable.wochentag,
                StundenplanTable.uhrzeit_von,
            )
        )
        rows = list(self._session.exec(stmt).all())
        return [_row_to_domain(r) for r in rows]

    def delete_by_wochentag(self, mandant_id: int, wochentag: int) -> bool:
        rows = list(
            self._session.exec(
                select(StundenplanTable)
                .where(StundenplanTable.mandant_id == mandant_id)
                .where(StundenplanTable.wochentag == wochentag)
            ).all()
        )
        for row in rows:
            self._session.delete(row)
        self._session.commit()
        return len(rows) > 0

    def delete_by_id(self, mandant_id: int, eintrag_id: int) -> bool:
        row = self._session.get(StundenplanTable, eintrag_id)
        if row is None or row.mandant_id != mandant_id:
            return False
        self._session.delete(row)
        self._session.commit()
        return True
