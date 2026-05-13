from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QObject, Signal

from Core.Application.betriebsferien_anwendung import BetriebsferienAnwendung
from Core.Domain.models.models_worktime import Betriebsferien
from External.Presentation.Desktop.betriebsferien_table_model import (
    BetriebsferienRow,
    BetriebsferienTableModel,
)


class BetriebsferienViewModel(QObject):
    status_changed = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, anwendung: BetriebsferienAnwendung) -> None:
        super().__init__()
        self._anwendung = anwendung
        self._table_model = BetriebsferienTableModel()

    @property
    def table_model(self) -> BetriebsferienTableModel:
        return self._table_model

    def lade_fuer_jahr(self, jahr: int) -> None:
        eintraege = self._anwendung.liste(jahr=jahr)
        rows = [
            BetriebsferienRow(
                id=eintrag.id,
                datum_von=eintrag.datum_von.strftime("%d.%m.%Y"),
                datum_bis=eintrag.datum_bis.strftime("%d.%m.%Y"),
                name=eintrag.betriebsferienname,
                anmerkung=eintrag.anmerkung or "",
            )
            for eintrag in eintraege
        ]
        self._table_model.set_rows(rows)
        self.status_changed.emit(f"{len(rows)} Eintraege geladen.")

    def speichere_eintrag(
        self,
        datum_von_text: str,
        datum_bis_text: str,
        name: str,
        anmerkung_text: str,
        eintrag_id: int | None = None,
    ) -> None:
        dv = datum_von_text.strip()
        db = datum_bis_text.strip()
        nm = name.strip()
        if not dv or not db:
            raise ValueError('"Von" und "Bis" sind erforderlich.')
        if not nm:
            raise ValueError("Bezeichnung ist erforderlich.")
        datum_von = datetime.strptime(dv, "%d.%m.%Y").date()
        datum_bis = datetime.strptime(db, "%d.%m.%Y").date()
        anm = anmerkung_text.strip()
        eintrag = Betriebsferien(
            id=eintrag_id,
            datum_von=datum_von,
            datum_bis=datum_bis,
            betriebsferienname=nm,
            anmerkung=anm or None,
        )
        self._anwendung.erfasse(eintrag)
        if eintrag_id is None:
            self.status_changed.emit("Betriebsferien gespeichert.")
        else:
            self.status_changed.emit("Betriebsferien aktualisiert.")

    def loesche_nach_id(self, eintrag_id: int | None) -> bool:
        if eintrag_id is None:
            self.error_occurred.emit("Ungueltige Auswahl (keine Id).")
            return False
        geloescht = self._anwendung.loesche(eintrag_id)
        if geloescht:
            self.status_changed.emit("Betriebsferien geloescht.")
        else:
            self.status_changed.emit("Eintrag nicht gefunden.")
        return geloescht
