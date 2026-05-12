from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QObject, Signal

from Core.Application.krankmeldung_anwendung import KrankmeldungAnwendung
from Core.Domain.models.models_worktime import Krankmeldung
from External.Presentation.Desktop.krankmeldung_table_model import (
    KrankmeldungRow,
    KrankmeldungTableModel,
)


class KrankmeldungViewModel(QObject):
    status_changed = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, anwendung: KrankmeldungAnwendung) -> None:
        super().__init__()
        self._anwendung = anwendung
        self._table_model = KrankmeldungTableModel()

    @property
    def table_model(self) -> KrankmeldungTableModel:
        return self._table_model

    def lade_fuer_jahr(self, jahr: int) -> None:
        eintraege = self._anwendung.liste(jahr=jahr)
        rows = [
            KrankmeldungRow(
                id=eintrag.id,
                krank_von=eintrag.krank_von.strftime("%d.%m.%Y"),
                krank_bis=eintrag.krank_bis.strftime("%d.%m.%Y"),
                krankmeldungstage=str(eintrag.krankmeldungstage),
            )
            for eintrag in eintraege
        ]
        self._table_model.set_rows(rows)
        self.status_changed.emit(f"{len(rows)} Krankmeldung(en) geladen.")

    def speichere_eintrag(
        self,
        krank_von_text: str,
        krank_bis_text: str,
        krankmeldungstage_text: str,
        eintrag_id: int | None = None,
    ) -> None:
        kv = krank_von_text.strip()
        kb = krank_bis_text.strip()
        if not kv or not kb:
            raise ValueError('"Krank von" und "Krank bis" sind erforderlich.')
        krank_von = datetime.strptime(kv, "%d.%m.%Y").date()
        krank_bis = datetime.strptime(kb, "%d.%m.%Y").date()
        stage_text = krankmeldungstage_text.strip()
        if not stage_text:
            raise ValueError("Anzahl Tage darf nicht leer sein.")
        krankmeldungstage = int(stage_text)
        eintrag = Krankmeldung(
            id=eintrag_id,
            krank_von=krank_von,
            krank_bis=krank_bis,
            krankmeldungstage=krankmeldungstage,
        )
        self._anwendung.erfasse(eintrag)
        if eintrag_id is None:
            self.status_changed.emit("Krankmeldung gespeichert.")
        else:
            self.status_changed.emit("Krankmeldung aktualisiert.")

    def loesche_nach_id(self, eintrag_id: int | None) -> bool:
        if eintrag_id is None:
            self.error_occurred.emit("Ungueltige Auswahl (keine Id).")
            return False
        geloescht = self._anwendung.loesche(eintrag_id)
        if geloescht:
            self.status_changed.emit("Krankmeldung geloescht.")
        else:
            self.status_changed.emit("Eintrag nicht gefunden.")
        return geloescht
