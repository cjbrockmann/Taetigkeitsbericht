"""Fußbereich des Zeiteinträge-Formulars (Überstunden + Urlaub, scrollt mit der Tabelle)."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QWidget

from External.Presentation.Desktop.zeiteintrag_ueberstunden_fuss import (
    ZeiteintragUeberstundenFussWidget,
)
from External.Presentation.Desktop.zeiteintrag_urlaub_fuss import ZeiteintragUrlaubFussWidget


class ZeiteintragFormularMonatsFuss(QWidget):
    """Zeile mit Überstunden- und Urlaub-Block unter der Monatstabelle."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 12, 0, 16)
        layout.setSpacing(16)

        self.ueberstunden = ZeiteintragUeberstundenFussWidget(self)
        self.urlaub = ZeiteintragUrlaubFussWidget(self)

        layout.addWidget(
            self.ueberstunden,
            1,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
        )
        layout.addWidget(
            self.urlaub,
            0,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
        )
        layout.addStretch(1)
