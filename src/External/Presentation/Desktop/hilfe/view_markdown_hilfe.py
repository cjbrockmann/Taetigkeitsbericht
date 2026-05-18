from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QWidget

from External.Presentation.Desktop.hilfe.hilfe_button import HilfeButton
from External.Presentation.Desktop.hilfe.readme_hilfe_dialog import (
    zeige_gemeinsame_markdown_hilfe,
)


class ViewMarkdownHilfe:
    """Hilfe-Button; öffnet die **gemeinsame** Markdown-Hilfe mit passender Datei."""

    __slots__ = ("_view", "_hilfedatei", "_tooltip", "_fenster_titel", "button", "__weakref__")

    def __init__(
        self,
        view: QWidget,
        *,
        hilfedatei: Path | str,
        tooltip: str,
        fenster_titel: str,
    ) -> None:
        self._view = view
        self._hilfedatei = hilfedatei
        self._tooltip = tooltip
        self._fenster_titel = fenster_titel
        self.button = HilfeButton(view, hilfedatei=hilfedatei, tooltip=tooltip)
        self.button.clicked.connect(self._on_clicked)

    def _on_clicked(self) -> None:
        QTimer.singleShot(0, self._oeffnen)

    def _oeffnen(self) -> None:
        zeige_gemeinsame_markdown_hilfe(
            self._view,
            hilfedatei=self._hilfedatei,
            tooltip=self._tooltip,
            fenster_titel=self._fenster_titel,
        )
