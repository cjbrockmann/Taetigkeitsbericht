"""Urlaubs-Zusammenfassung unter der Zeiteintrag-Tabelle."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from External.Presentation.Desktop.zeiteintrag_monats_fuss_basis import (
    HINWEIS_STIL,
    RAHMEN_STIL,
    WERT_MOCK_STIL,
)

URLAUB_FUSS_MIN_BREITE = 200
URLAUB_FUSS_MAX_BREITE = 230


class ZeiteintragUrlaubFussWidget(QFrame):
    """Rechte Zusammenfassung: Urlaubsanspruch (Mockup)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("monatsFussRahmen")
        self.setStyleSheet(RAHMEN_STIL)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum)
        self.setMinimumWidth(URLAUB_FUSS_MIN_BREITE)
        self.setMaximumWidth(URLAUB_FUSS_MAX_BREITE)

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 8)
        root.setSpacing(4)

        titel = QLabel("Erholungsurlaub", self)
        font = titel.font()
        font.setBold(True)
        titel.setFont(font)
        titel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(titel)

        grid = QGridLayout()
        grid.setContentsMargins(0, 8, 0, 0)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(6)

        zeilen = (
            ("Resturlaub 2025 *", "4"),
            ("Jahresurlaub 2026 *", "24"),
            ("Zusatzurlaub SGB IX *", "0"),
            ("Gesamturlaub 2026 *", "28"),
            ("genommener Urlaub *", "7"),
        )
        for row, (text, wert) in enumerate(zeilen):
            beschriftung = QLabel(text, self)
            wert_label = QLabel(wert, self)
            wert_label.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            wert_label.setStyleSheet(WERT_MOCK_STIL)
            grid.addWidget(beschriftung, row, 0)
            grid.addWidget(wert_label, row, 1)

        trenner = QFrame(self)
        trenner.setFrameShape(QFrame.Shape.HLine)
        trenner.setFrameShadow(QFrame.Shadow.Sunken)
        root.addLayout(grid)
        root.addWidget(trenner)

        anspruch = QHBoxLayout()
        anspruch.addWidget(QLabel("Anspruch 2026 *", self))
        anspruch_wert = QLabel("21", self)
        anspruch_wert.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        anspruch_wert.setStyleSheet(WERT_MOCK_STIL)
        anspruch.addStretch(1)
        anspruch.addWidget(anspruch_wert)
        root.addLayout(anspruch)

        hinweis = QLabel("Mockup – laufender Urlaubsanspruch folgt", self)
        hinweis.setStyleSheet(HINWEIS_STIL)
        hinweis.setWordWrap(True)
        root.addWidget(hinweis)
