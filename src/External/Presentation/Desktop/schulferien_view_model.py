from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QObject, Signal

from Core.Application.schulferien_anwendung import SchulferienAnwendung
from Core.Domain.models.models_worktime import Schulferien
from External.Presentation.Desktop.schulferien_table_model import (
    SchulferienRow,
    SchulferienTableModel,
)


class SchulferienViewModel(QObject):
    status_changed = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, anwendung: SchulferienAnwendung) -> None:
        super().__init__()
        self._anwendung = anwendung
        self._table_model = SchulferienTableModel()

    @property
    def table_model(self) -> SchulferienTableModel:
        return self._table_model

    def lade_fuer_jahr(self, jahr: int) -> None:
        n = self._refresh_tabelle(jahr)
        self.status_changed.emit(f"{n} Einträge geladen.")

    def _refresh_tabelle(self, jahr: int) -> int:
        eintraege = self._anwendung.liste(jahr=jahr)
        rows = [
            SchulferienRow(
                id=eintrag.id,
                datum_von=eintrag.datum_von.strftime("%d.%m.%Y"),
                datum_bis=eintrag.datum_bis.strftime("%d.%m.%Y"),
                name=eintrag.schulferienname,
                anmerkung=eintrag.anmerkung or "",
            )
            for eintrag in eintraege
        ]
        self._table_model.set_rows(rows)
        return len(rows)

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
        eintrag = Schulferien(
            id=eintrag_id,
            datum_von=datum_von,
            datum_bis=datum_bis,
            schulferienname=nm,
            anmerkung=anm or None,
        )
        self._anwendung.erfasse(eintrag)
        if eintrag_id is None:
            self.status_changed.emit("Schulferien gespeichert.")
        else:
            self.status_changed.emit("Schulferien aktualisiert.")

    def loesche_nach_id(self, eintrag_id: int | None) -> bool:
        if eintrag_id is None:
            self.error_occurred.emit("Ungültige Auswahl (keine Id).")
            return False
        geloescht = self._anwendung.loesche(eintrag_id)
        if geloescht:
            self.status_changed.emit("Schulferien gelöscht.")
        else:
            self.status_changed.emit("Eintrag nicht gefunden.")
        return geloescht

    def lade_aus_api_und_speichere(self, jahr: int) -> None:
        try:
            neu, aktualisiert, uebersprungen = self._anwendung.importiere_aus_api(jahr=jahr)
        except (OSError, ValueError) as exc:
            self.error_occurred.emit(str(exc))
            return
        n = self._refresh_tabelle(jahr)
        teile = [f"{neu} neu", f"{aktualisiert} aktualisiert"]
        if uebersprungen:
            teile.append(f"{uebersprungen} übersprungen (Überschneidung)")
        self.status_changed.emit(
            f"{', '.join(teile)} (Schulferien-API). {n} Einträge für {jahr} angezeigt."
        )
