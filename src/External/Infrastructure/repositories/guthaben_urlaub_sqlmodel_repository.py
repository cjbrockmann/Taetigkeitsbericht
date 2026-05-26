from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy import extract
from sqlmodel import Session, select

from Core.Domain.models.models_worktime import GuthabenUrlaub
from External.Infrastructure.sqlmodel_tables import GuthabenUrlaubTable


def _row_to_domain(row: GuthabenUrlaubTable) -> GuthabenUrlaub:
    return GuthabenUrlaub(
        id=row.id,
        mandant_id=row.mandant_id,
        datum=row.datum,
        urlaubstage_guthaben_vorjahr=row.urlaubstage_guthaben_vorjahr,
        urlaubstage_guthaben_vormonat=row.urlaubstage_guthaben_vormonat,
        urlaubstage_im_monat_aktuell=row.urlaubstage_im_monat_aktuell,
        guthaben_vormonat_korrektur=row.guthaben_vormonat_korrektur,
    )


class SqlGuthabenUrlaubRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, eintrag: GuthabenUrlaub) -> GuthabenUrlaub:
        if eintrag.mandant_id is None:
            raise ValueError("mandant_id ist fuer GuthabenUrlaub erforderlich.")
        row: GuthabenUrlaubTable | None = None
        if eintrag.id is not None:
            row = self._session.get(GuthabenUrlaubTable, eintrag.id)
        if row is None:
            row = GuthabenUrlaubTable(
                id=eintrag.id,
                mandant_id=eintrag.mandant_id,
                datum=eintrag.datum,
                urlaubstage_guthaben_vorjahr=eintrag.urlaubstage_guthaben_vorjahr,
                urlaubstage_guthaben_vormonat=eintrag.urlaubstage_guthaben_vormonat,
                urlaubstage_im_monat_aktuell=eintrag.urlaubstage_im_monat_aktuell,
                guthaben_vormonat_korrektur=eintrag.guthaben_vormonat_korrektur,
            )
            self._session.add(row)
        else:
            if row.mandant_id != eintrag.mandant_id:
                raise ValueError("GuthabenUrlaub gehoert zu einem anderen Mandanten.")
            row.datum = eintrag.datum
            row.urlaubstage_guthaben_vorjahr = eintrag.urlaubstage_guthaben_vorjahr
            row.urlaubstage_guthaben_vormonat = eintrag.urlaubstage_guthaben_vormonat
            row.urlaubstage_im_monat_aktuell = eintrag.urlaubstage_im_monat_aktuell
            row.guthaben_vormonat_korrektur = eintrag.guthaben_vormonat_korrektur
        self._session.commit()
        self._session.refresh(row)
        return _row_to_domain(row)

    def get_by_id(self, mandant_id: int, eintrag_id: int) -> Optional[GuthabenUrlaub]:
        row = self._session.get(GuthabenUrlaubTable, eintrag_id)
        if row is None or row.mandant_id != mandant_id:
            return None
        return _row_to_domain(row)

    def get_by_mandant_und_datum(
        self, mandant_id: int, datum: date
    ) -> Optional[GuthabenUrlaub]:
        stmt = (
            select(GuthabenUrlaubTable)
            .where(GuthabenUrlaubTable.mandant_id == mandant_id)
            .where(GuthabenUrlaubTable.datum == datum)
        )
        row = self._session.exec(stmt).first()
        if row is None:
            return None
        return _row_to_domain(row)

    def list_all(self, mandant_id: int, jahr: Optional[int] = None) -> list[GuthabenUrlaub]:
        stmt = (
            select(GuthabenUrlaubTable)
            .where(GuthabenUrlaubTable.mandant_id == mandant_id)
            .order_by(GuthabenUrlaubTable.datum, GuthabenUrlaubTable.id)
        )
        if jahr is not None:
            stmt = stmt.where(extract("year", GuthabenUrlaubTable.datum) == jahr)
        rows = list(self._session.exec(stmt).all())
        return [_row_to_domain(r) for r in rows]

    def delete_by_id(self, mandant_id: int, eintrag_id: int) -> bool:
        row = self._session.get(GuthabenUrlaubTable, eintrag_id)
        if row is None or row.mandant_id != mandant_id:
            return False
        self._session.delete(row)
        self._session.commit()
        return True
