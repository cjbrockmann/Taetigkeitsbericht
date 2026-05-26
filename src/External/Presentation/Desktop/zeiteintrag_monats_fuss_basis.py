"""Gemeinsame Hilfen für die Monats-Zusammenfassung unter der Zeiteintrag-Tabelle."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QHBoxLayout, QSizePolicy, QWidget

MONATSNAMEN = (
    "",
    "Januar",
    "Februar",
    "März",
    "April",
    "Mai",
    "Juni",
    "Juli",
    "August",
    "September",
    "Oktober",
    "November",
    "Dezember",
)

RAHMEN_STIL = (
    "QFrame#monatsFussRahmen {"
    "  border: 2px solid #333;"
    "  background: palette(base);"
    "}"
)

WERT_NEGATIV_STIL = "color: #c00000; font-style: italic;"
WERT_MOCK_STIL = "color: palette(mid); font-style: italic;"
HINWEIS_STIL = "color: palette(mid); font-size: 9pt;"


class WertZeile(QWidget):
    def __init__(
        self,
        beschriftung: str,
        wert: str,
        *,
        negativ: bool = False,
        mock: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(12)

        label = QLabel(beschriftung, self)
        label.setWordWrap(True)
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        wert_label = QLabel(wert, self)
        wert_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        wert_label.setMinimumWidth(72)
        if negativ:
            wert_label.setStyleSheet(WERT_NEGATIV_STIL)
        elif mock:
            wert_label.setStyleSheet(WERT_MOCK_STIL)

        layout.addWidget(label, 1)
        layout.addWidget(wert_label, 0)

        self._beschriftung_label = label
        self._wert_label = wert_label

    def set_beschriftung(self, text: str) -> None:
        self._beschriftung_label.setText(text)

    def set_wert(self, text: str, *, negativ: bool = False, mock: bool = False) -> None:
        self._wert_label.setText(text)
        if negativ:
            self._wert_label.setStyleSheet(WERT_NEGATIV_STIL)
        elif mock:
            self._wert_label.setStyleSheet(WERT_MOCK_STIL)
        else:
            self._wert_label.setStyleSheet("")
