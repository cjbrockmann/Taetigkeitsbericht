"""Überstunden-/Stunden-Zusammenfassung unter der Zeiteintrag-Tabelle."""

from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout, QWidget

from Core.Application.zeiteintrag_dto_guthabenberechnung_helper import (
    GuthabenVerrechnungErgebnis,
)
from External.Presentation.Desktop.zeiteintrag_monats_fuss_basis import (
    MONATSNAMEN,
    RAHMEN_STIL,
    WertZeile,
)

UEBERSTUNDEN_FUSS_MIN_BREITE = 440
UEBERSTUNDEN_FUSS_MAX_BREITE = 600


class ZeiteintragUeberstundenFussWidget(QFrame):
    """Linke Zusammenfassung: Ist/Soll und Zeitguthaben/-defizit je Monat."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("monatsFussRahmen")
        self.setStyleSheet(RAHMEN_STIL)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self.setMinimumWidth(UEBERSTUNDEN_FUSS_MIN_BREITE)
        self.setMaximumWidth(UEBERSTUNDEN_FUSS_MAX_BREITE)

        root = QVBoxLayout(self)
        root.setContentsMargins(4, 8, 4, 8)
        root.setSpacing(2)

        self._ist = WertZeile("Ist-Arbeitsstunden", "00:00")
        self._guthaben_vormonat = WertZeile("zzgl. Zeitguthaben Vormonat", "00:00")
        self._defizit_vormonat = WertZeile(
            "abzgl. Zeitdefizit Vormonat", "00:00", negativ=True
        )
        self._soll_stundenplan = WertZeile("abzgl. Soll-Arbeitsstunden (Stundenplan)", "00:00")
        self._soll_vertrag = WertZeile("abzgl. Soll nach Vertrag", "00:00")

        trenner = QFrame(self)
        trenner.setFrameShape(QFrame.Shape.HLine)
        trenner.setFrameShadow(QFrame.Shadow.Sunken)

        self._guthaben_monat = WertZeile("Zeitguthaben Monat", "00:00")
        self._defizit_monat = WertZeile("Zeitdefizit Monat", "00:00", negativ=True)

        for zeile in (
            self._ist,
            self._guthaben_vormonat,
            self._defizit_vormonat,
            self._soll_stundenplan,
            self._soll_vertrag,
            trenner,
            self._guthaben_monat,
            self._defizit_monat,
        ):
            root.addWidget(zeile)

    def set_monat(self, jahr: int, monat: int) -> None:
        _ = jahr
        name = MONATSNAMEN[monat] if 1 <= monat <= 12 else f"{monat:02d}"
        self._guthaben_monat.set_beschriftung(f"Zeitguthaben {name}")
        self._defizit_monat.set_beschriftung(f"Zeitdefizit {name}")

    def set_stunden_summen(
        self,
        geleistet: str,
        soll_stundenplan: str,
        soll_vertrag: str,
    ) -> None:
        self._ist.set_wert(geleistet)
        self._soll_stundenplan.set_wert(soll_stundenplan)
        self._soll_vertrag.set_wert(soll_vertrag)

    def set_guthaben_verrechnung(self, ergebnis: GuthabenVerrechnungErgebnis) -> None:
        hh = GuthabenVerrechnungErgebnis.stunden_als_hh_mm
        self._guthaben_vormonat.set_wert(hh(ergebnis.guthaben_vormonat_stunden))
        self._defizit_vormonat.set_wert(
            hh(ergebnis.defizit_vormonat_stunden), negativ=ergebnis.defizit_vormonat_stunden > 0
        )
        self._guthaben_monat.set_wert(hh(ergebnis.guthaben_monat_stunden))
        self._defizit_monat.set_wert(
            hh(ergebnis.defizit_monat_stunden), negativ=ergebnis.defizit_monat_stunden > 0
        )
