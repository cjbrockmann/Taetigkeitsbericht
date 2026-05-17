from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QObject, Signal

from Core.Application.feiertag_anwendung import FeiertagAnwendung
from Core.Domain.models.models_worktime import Feiertag
from External.Presentation.Desktop.feiertag_registry import FeiertagRegistry
from External.Presentation.Desktop.feiertag_table_model import FeiertagRow, FeiertagTableModel


class FeiertagViewModel(QObject):
    status_changed = Signal(str)
    error_occurred = Signal(str)

    def __init__(
        self,
        anwendung: FeiertagAnwendung,
        feiertag_registry: FeiertagRegistry,
    ) -> None:
        super().__init__()
        self._anwendung = anwendung
        self._feiertag_registry = feiertag_registry
        self._table_model = FeiertagTableModel()
        self._geladenes_jahr: int | None = None

    @property
    def table_model(self) -> FeiertagTableModel:
        return self._table_model

    def lade_fuer_jahr(self, jahr: int) -> None:
        eintraege = self._anwendung.liste(jahr=jahr)
        self._geladenes_jahr = jahr
        self._feiertag_registry.aktualisiere_jahr(jahr, eintraege, benachrichtigen=True)
        rows = [
            FeiertagRow(
                datum=eintrag.datum.strftime("%d.%m.%Y"),
                feiertagsname=eintrag.feiertagsname,
                ist_halber_tag=eintrag.ist_halber_tag,
                ist_offiziell=eintrag.ist_offiziell,
                hinweis=eintrag.hinweis or "",
            )
            for eintrag in eintraege
        ]
        self._table_model.set_rows(rows)
        self.status_changed.emit(f"{len(rows)} Feiertag(e) geladen.")

    def lade_aus_api_und_speichere(self, jahr: int) -> None:
        neu, aktualisiert = self._anwendung.lade_aus_api(jahr=jahr)
        self.status_changed.emit(
            f"{neu} Feiertag(e) neu gespeichert, {aktualisiert} aktualisiert (Internet-Import)."
        )
        self.lade_fuer_jahr(jahr)

    def fuege_feiertag_hinzu(
        self,
        datum_text: str,
        bezeichnung: str,
        ist_halber_tag: bool,
        ist_offiziell: bool,
    ) -> None:
        text_datum = datum_text.strip()
        text_bezeichnung = bezeichnung.strip()
        if not text_datum:
            raise ValueError("Datum darf nicht leer sein.")
        if not text_bezeichnung:
            raise ValueError("Bezeichnung darf nicht leer sein.")
        datum = datetime.strptime(text_datum, "%d.%m.%Y").date()
        self._anwendung.erfasse(
            Feiertag(
                datum=datum,
                feiertagsname=text_bezeichnung,
                ist_halber_tag=ist_halber_tag,
                ist_offiziell=ist_offiziell,
            )
        )
        self.status_changed.emit("Feiertag gespeichert.")
        if self._geladenes_jahr == datum.year:
            self.lade_fuer_jahr(datum.year)

    def speichere_zeile(self, row_index: int) -> None:
        if row_index < 0 or row_index >= len(self._table_model.rows):
            return
        row = self._table_model.rows[row_index]
        datum = datetime.strptime(row.datum.strip(), "%d.%m.%Y").date()
        self._anwendung.aktualisiere(
            Feiertag(
                datum=datum,
                feiertagsname=row.feiertagsname,
                hinweis=row.hinweis.strip() or None,
                ist_halber_tag=row.ist_halber_tag,
                ist_offiziell=row.ist_offiziell,
            )
        )
        if self._geladenes_jahr is not None:
            self._feiertag_registry.aktualisiere_jahr(
                self._geladenes_jahr,
                self._anwendung.liste(jahr=self._geladenes_jahr),
                benachrichtigen=True,
            )

    def loesche_nach_datum(self, datum_text: str) -> bool:
        text_datum = datum_text.strip()
        if not text_datum:
            return False
        datum = datetime.strptime(text_datum, "%d.%m.%Y").date()
        geloescht = self._anwendung.loesche_fuer_datum(datum)
        if geloescht:
            self.status_changed.emit("Eintrag geloescht.")
        else:
            self.status_changed.emit("Kein Eintrag zum Datum gefunden.")
        return geloescht
