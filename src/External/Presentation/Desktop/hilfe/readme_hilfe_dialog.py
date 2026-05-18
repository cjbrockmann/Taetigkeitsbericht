from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QDialog, QVBoxLayout, QWidget
from QMarkdownView import MarkdownView

from External.Presentation.Desktop.hilfe.hilfedatei_pfad import hilfedatei_zu_pfad

_MARKDOWN_EXTENSIONS = [
    "markdown.extensions.tables",
    "markdown.extensions.fenced_code",
    "markdown.extensions.extra",
]


def _markdown_inhalt(pfad: Path) -> str:
    if pfad.is_file():
        return pfad.read_text(encoding="utf-8")
    return "# Hilfe\n\nDie Hilfedatei konnte nicht geladen werden. Bitte wenden Sie sich an den Support."


class ReadmeHilfeDialog(QDialog):
    """Dialog mit Markdown-Ansicht; wiederverwendbar pro Hilfedatei.

    Unter Windows sollte ``parent=None`` verwendet werden (Hilfe als eigenes
    Top-Level-Fenster), damit die eingebettete QWebEngineView nicht das
    Hauptfenster kurz minimieren/wiederherstellen lässt. Anschließend
    :meth:`zentriere_ueber` mit dem Hauptfenster aufrufen.
    """

    def __init__(
        self,
        parent=None,
        *,
        hilfedatei: Path | str,
        tooltip: str,
        fenster_titel: str | None = None,
    ) -> None:
        super().__init__(parent)
        titel = fenster_titel if fenster_titel is not None else tooltip
        self.setWindowTitle(titel)
        self.setToolTip(tooltip)
        self.resize(920, 720)
        self._inhalt_geladen = False
        self._pfad = hilfedatei_zu_pfad(hilfedatei)
        self._inhalt = _markdown_inhalt(self._pfad)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        self._markdown = MarkdownView(self)
        self._markdown.setExtensions(_MARKDOWN_EXTENSIONS)
        layout.addWidget(self._markdown)
        self._markdown.loadFinished.connect(self._on_markdown_view_loaded)

    def zentriere_ueber(self, bezugsfenster: QWidget) -> None:
        """Positioniert den Dialog über dem Rahmen des Bezugsfensters (meist das Hauptfenster)."""
        fenster = bezugsfenster.window()
        wg = fenster.frameGeometry()
        x = wg.center().x() - self.width() // 2
        y = wg.center().y() - self.height() // 2
        screen = bezugsfenster.screen()
        if screen is not None:
            ag = screen.availableGeometry()
            x = max(ag.left(), min(x, ag.right() - self.width() + 1))
            y = max(ag.top(), min(y, ag.bottom() - self.height() + 1))
        self.move(x, y)

    def _on_markdown_view_loaded(self, ok: bool) -> None:
        if not ok or self._inhalt_geladen:
            return
        self._inhalt_geladen = True
        self._markdown.setValue(self._inhalt)
