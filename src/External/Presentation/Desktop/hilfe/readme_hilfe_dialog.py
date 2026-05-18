from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QTimer
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
    """Dialog mit Markdown-Ansicht.

    Unter Windows sollte ``parent=None`` verwendet werden (Hilfe als eigenes
    Top-Level-Fenster), damit die eingebettete QWebEngineView nicht das
    Hauptfenster kurz minimieren/wiederherstellen lässt. Anschließend
    :meth:`zentriere_ueber` mit dem Hauptfenster aufrufen.

    Für die gesamte Anwendung wird **ein** Dialog über
    :func:`zeige_gemeinsame_markdown_hilfe` wiederverwendet; der Inhalt wechselt
    je nach aufgerufener Hilfedatei.
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
        self._inhalt_geladen = False
        self._pfad = Path()
        self._inhalt = ""
        self.resize(920, 720)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        self._markdown = MarkdownView(self)
        self._markdown.setExtensions(_MARKDOWN_EXTENSIONS)
        layout.addWidget(self._markdown)
        self._markdown.loadFinished.connect(self._on_markdown_view_loaded)

        self.wechsle_inhalt(hilfedatei, tooltip, fenster_titel)

    def wechsle_inhalt(
        self,
        hilfedatei: Path | str,
        tooltip: str,
        fenster_titel: str | None = None,
    ) -> None:
        """Lädt andere Hilfedatei und aktualisiert Titel; Markdown nach WebEngine-Start."""
        self.setToolTip(tooltip)
        titel = fenster_titel if fenster_titel is not None else tooltip
        self.setWindowTitle(titel)
        self._pfad = hilfedatei_zu_pfad(hilfedatei)
        self._inhalt = _markdown_inhalt(self._pfad)
        if self._inhalt_geladen:
            self._markdown.setValue(self._inhalt)

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


_gemeinsamer_hilfe_dialog: ReadmeHilfeDialog | None = None


def zeige_gemeinsame_markdown_hilfe(
    bezugsfenster: QWidget,
    *,
    hilfedatei: Path | str,
    tooltip: str,
    fenster_titel: str,
) -> None:
    """Genau ein Hilfefenster für die App: Inhalt wechseln, Dialog nach vorn."""
    global _gemeinsamer_hilfe_dialog
    if _gemeinsamer_hilfe_dialog is None:
        _gemeinsamer_hilfe_dialog = ReadmeHilfeDialog(
            None,
            hilfedatei=hilfedatei,
            tooltip=tooltip,
            fenster_titel=fenster_titel,
        )
    else:
        _gemeinsamer_hilfe_dialog.wechsle_inhalt(
            hilfedatei, tooltip, fenster_titel
        )
    _gemeinsamer_hilfe_dialog.zentriere_ueber(bezugsfenster)
    _gemeinsamer_hilfe_dialog.show()
    _gemeinsamer_hilfe_dialog.raise_()
    QTimer.singleShot(0, _gemeinsamer_hilfe_dialog.activateWindow)


def schliesse_gemeinsame_markdown_hilfe() -> None:
    """Schließt das app-weite Hilfefenster (z. B. beim Beenden des Hauptprogramms)."""
    global _gemeinsamer_hilfe_dialog
    if _gemeinsamer_hilfe_dialog is None:
        return
    _gemeinsamer_hilfe_dialog.close()
    _gemeinsamer_hilfe_dialog.deleteLater()
    _gemeinsamer_hilfe_dialog = None
