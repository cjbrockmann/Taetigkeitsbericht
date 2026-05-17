from __future__ import annotations

import math
from datetime import datetime

from PySide6.QtCore import QObject, Signal

from Core.Application.urlaubsantrag_anwendung import UrlaubsantragAnwendung
from Core.Domain.models.models_worktime import Urlaubsantrag
from External.Presentation.Desktop.urlaubsantrag_table_model import (
    UrlaubsantragRow,
    UrlaubsantragTableModel,
)


def _urlaubstage_anzeige(v: float) -> str:
    if math.isclose(v, round(v)):
        return str(int(round(v)))
    return f"{v:.1f}".replace(".", ",")


class UrlaubsantragViewModel(QObject):
    status_changed = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, anwendung: UrlaubsantragAnwendung) -> None:
        super().__init__()
        self._anwendung = anwendung
        self._table_model = UrlaubsantragTableModel()

    @property
    def table_model(self) -> UrlaubsantragTableModel:
        return self._table_model

    def lade_fuer_jahr(self, jahr: int) -> None:
        eintraege = self._anwendung.liste(jahr=jahr)
        rows = [
            UrlaubsantragRow(
                id=eintrag.id,
                datum_von=eintrag.datum_von.strftime("%d.%m.%Y"),
                datum_bis=eintrag.datum_bis.strftime("%d.%m.%Y"),
                urlaubstyp=eintrag.urlaubstyp,
                urlaubstage=_urlaubstage_anzeige(float(eintrag.urlaubstage)),
                genehmigt="Ja" if eintrag.genehmigt else "Nein",
            )
            for eintrag in eintraege
        ]
        self._table_model.set_rows(rows)
        self.status_changed.emit(f"{len(rows)} Urlaubsantrag/-anträge geladen.")

    def speichere_antrag(
        self,
        datum_von_text: str,
        datum_bis_text: str,
        urlaubstyp: str,
        urlaubstage_text: str,
        genehmigt: bool,
        antrag_id: int | None = None,
    ) -> None:
        dv = datum_von_text.strip()
        db = datum_bis_text.strip()
        typ = urlaubstyp.strip()
        if not dv or not db:
            raise ValueError("Datum von und Datum bis sind erforderlich.")
        if not typ:
            raise ValueError("Urlaubstyp darf nicht leer sein.")
        datum_von = datetime.strptime(dv, "%d.%m.%Y").date()
        datum_bis = datetime.strptime(db, "%d.%m.%Y").date()
        stage_text = urlaubstage_text.strip().replace(",", ".")
        if not stage_text:
            raise ValueError("Anzahl Urlaubstage darf nicht leer sein.")
        try:
            urlaubstage = float(stage_text)
        except ValueError as exc:
            raise ValueError("Urlaubstage muss eine Zahl sein (z. B. 1 oder 1.5).") from exc
        antrag = Urlaubsantrag(
            id=antrag_id,
            datum_von=datum_von,
            datum_bis=datum_bis,
            urlaubstyp=typ,
            urlaubstage=urlaubstage,
            genehmigt=genehmigt,
        )
        self._anwendung.erfasse(antrag)
        if antrag_id is not None:
            self.status_changed.emit("Urlaubsantrag aktualisiert.")
        else:
            self.status_changed.emit("Urlaubsantrag gespeichert.")

    def loesche_nach_id(self, antrag_id: int | None) -> bool:
        if antrag_id is None:
            self.error_occurred.emit("Ungültige Auswahl (keine Id).")
            return False
        geloescht = self._anwendung.loesche(antrag_id)
        if geloescht:
            self.status_changed.emit("Urlaubsantrag gelöscht.")
        else:
            self.status_changed.emit("Eintrag nicht gefunden.")
        return geloescht
