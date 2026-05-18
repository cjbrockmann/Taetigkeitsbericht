from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton

from External.Presentation.Desktop.hilfe.hilfedatei_pfad import hilfedatei_zu_pfad


class HilfeButton(QPushButton):
    """Runder Hilfe-Button mit blauem Hintergrund und weißem Fragezeichen."""

    _GROESSE = 16

    def __init__(
        self,
        parent=None,
        *,
        hilfedatei: Path | str,
        tooltip: str,
    ) -> None:
        super().__init__("?", parent)
        self._hilfedatei_pfad = hilfedatei_zu_pfad(hilfedatei)
        self.setFixedSize(self._GROESSE, self._GROESSE)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(tooltip)
        radius = self._GROESSE // 2
        self.setStyleSheet(
            f"""
            QPushButton {{
                background-color: #1976D2;
                color: white;
                border: none;
                border-radius: {radius}px;
                font-weight: bold;
                font-size: 12px;
                padding: 0; margin-left: 10px;
                min-width: {self._GROESSE}px;
                max-width: {self._GROESSE}px;
                min-height: {self._GROESSE}px;
                max-height: {self._GROESSE}px;
            }}
            QPushButton:hover {{
                background-color: #1565C0;
            }}
            QPushButton:pressed {{
                background-color: #0D47A1;
            }}
            """
        )

    @property
    def hilfedatei_pfad(self) -> Path:
        """Aufgelöster Pfad zur Markdown-Hilfedatei (wie beim Dialog)."""
        return self._hilfedatei_pfad
