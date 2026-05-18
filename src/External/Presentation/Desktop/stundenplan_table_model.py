from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor

from External.Presentation.Desktop.table_view_styles import (
    DIRTY_ROW_TEXT_COLOR,
    NORMAL_ROW_TEXT_COLOR,
)
from External.Presentation.Desktop.arbeitszeit_berechnung import (
    minuten_als_hh_mm,
    netto_arbeitsminuten,
    parse_uhrzeit_minuten,
)


WOCHENTAG_LABELS: list[tuple[int, str]] = [
    (1, "Mo"),
    (2, "Di"),
    (3, "Mi"),
    (4, "Do"),
    (5, "Fr"),
    (6, "Sa"),
    (7, "So"),
]


@dataclass
class StundenplanRow:
    id: int | None = None
    wochentag: int = 1
    uhrzeit_von: str = ""
    uhrzeit_bis: str = ""
    pause_beginn: str = ""
    pause_ende: str = ""
    pause2_beginn: str = ""
    pause2_ende: str = ""
    anmerkung: str = ""


class StundenplanTableModel(QAbstractTableModel):
    HEADERS = [
        "Tag",
        "Von",
        "Bis",
        "Von",
        "Bis",
        "Von",
        "Bis",
        "Soll",
        "Kommentar",
    ]
    HEADER_TOOLTIPS = [
        "Wochentag (Mo-So)",
        "Erwartetes Format: HH:MM, z. B. 08:30",
        "Erwartetes Format: HH:MM, z. B. 17:00",
        "Optionales Format: HH:MM, z. B. 12:00",
        "Optionales Format: HH:MM, z. B. 12:30",
        "Optionales Format: HH:MM, z. B. 14:00",
        "Optionales Format: HH:MM, z. B. 14:15",
        "Zu leistende Zeit (Bis - Von - beide Pausen), Format HH:MM",
        "Freitext (max. 80 Zeichen)",
    ]

    def __init__(self) -> None:
        super().__init__()
        self._rows: list[StundenplanRow] = []
        self._dirty_rows: set[int] = set()

    @property
    def rows(self) -> list[StundenplanRow]:
        return self._rows

    def set_rows(self, rows: list[StundenplanRow]) -> None:
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        if parent.isValid():
            return 0
        return len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        if parent.isValid():
            return 0
        return len(self.HEADERS)

    def headerData(  # noqa: N802
        self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole
    ) -> str | None:
        if section < 0:
            return None

        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section >= len(self.HEADERS):
                return None
            return self.HEADERS[section]
        if orientation == Qt.Horizontal and role == Qt.ToolTipRole:
            if section >= len(self.HEADER_TOOLTIPS):
                return None
            return self.HEADER_TOOLTIPS[section]
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            if section >= len(self._rows):
                return None
            return str(section + 1)
        return None

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> str | QColor | int | None:
        if not index.isValid():
            return None
        row = self._rows[index.row()]
        if role == Qt.BackgroundRole:
            if row.wochentag in (6, 7):
                return QColor("#eeeeee")
            return QColor("#ffffff")
        if role == Qt.ForegroundRole:
            if index.row() in self._dirty_rows:
                return QColor(DIRTY_ROW_TEXT_COLOR)
            return QColor(NORMAL_ROW_TEXT_COLOR)
        if role == Qt.EditRole and index.column() == 0:
            return row.wochentag
        if role not in (Qt.DisplayRole, Qt.EditRole):
            return None
        match index.column():
            case 0:
                return _label_for_wochentag(row.wochentag)
            case 1:
                return row.uhrzeit_von
            case 2:
                return row.uhrzeit_bis
            case 3:
                return row.pause_beginn
            case 4:
                return row.pause_ende
            case 5:
                return row.pause2_beginn
            case 6:
                return row.pause2_ende
            case 7:
                return self._calculate_zuleistende_zeit(
                    row.uhrzeit_von,
                    row.uhrzeit_bis,
                    row.pause_beginn,
                    row.pause_ende,
                    row.pause2_beginn,
                    row.pause2_ende,
                )
            case 8:
                return row.anmerkung
            case _:
                return None

    def setData(self, index: QModelIndex, value: object, role: int = Qt.EditRole) -> bool:  # noqa: N802
        if not index.isValid() or role != Qt.EditRole:
            return False

        row = self._rows[index.row()]
        if index.column() == 0:
            wochentag = self._coerce_wochentag(value)
            if wochentag is None:
                return False
            row.wochentag = wochentag
            left = self.index(index.row(), 0)
            right = self.index(index.row(), len(self.HEADERS) - 1)
            self.dataChanged.emit(
                left, right, [Qt.DisplayRole, Qt.EditRole, Qt.BackgroundRole]
            )
            return True

        text = str(value)
        if index.column() != 8:
            text = text.strip()
        if index.column() == 1:
            row.uhrzeit_von = text
        elif index.column() == 2:
            row.uhrzeit_bis = text
        elif index.column() == 3:
            row.pause_beginn = text
        elif index.column() == 4:
            row.pause_ende = text
        elif index.column() == 5:
            row.pause2_beginn = text
        elif index.column() == 6:
            row.pause2_ende = text
        elif index.column() == 7:
            return False
        elif index.column() == 8:
            row.anmerkung = text
        else:
            return False

        if index.column() in (1, 2, 3, 4, 5, 6):
            left = self.index(index.row(), index.column())
            right = self.index(index.row(), 7)
            self.dataChanged.emit(
                left, right, [Qt.DisplayRole, Qt.EditRole, Qt.BackgroundRole]
            )
            return True

        self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole, Qt.BackgroundRole])
        return True

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.ItemIsEnabled
        if index.column() == 7:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    def add_empty_row(self, position: int | None = None, wochentag: int = 1) -> int:
        if position is None or position < 0 or position > len(self._rows):
            position = len(self._rows)
        if not 1 <= wochentag <= 7:
            wochentag = 1
        self.beginInsertRows(QModelIndex(), position, position)
        self._rows.insert(position, StundenplanRow(wochentag=wochentag))
        self.endInsertRows()
        return position

    def remove_rows(self, row_indices: list[int]) -> None:
        for row_index in sorted(set(row_indices), reverse=True):
            if row_index < 0 or row_index >= len(self._rows):
                continue
            self.beginRemoveRows(QModelIndex(), row_index, row_index)
            del self._rows[row_index]
            self.endRemoveRows()

    def set_dirty_rows(self, dirty_rows: set[int]) -> None:
        if self._dirty_rows == dirty_rows:
            return
        self._dirty_rows = set(dirty_rows)
        self.repaint_dirty_rows()

    def repaint_dirty_rows(self) -> None:
        if not self._rows:
            return
        top_left = self.index(0, 0)
        bottom_right = self.index(len(self._rows) - 1, len(self.HEADERS) - 1)
        self.dataChanged.emit(top_left, bottom_right, [Qt.ForegroundRole])

    def is_row_dirty(self, row_index: int) -> bool:
        return row_index in self._dirty_rows

    def summe_zuleistende_minuten(self) -> int:
        """Summe der Spalte Soll (zu leistende Zeit) ueber alle Zeilen."""
        summe = 0
        for row in self._rows:
            netto = netto_arbeitsminuten(
                row.uhrzeit_von,
                row.uhrzeit_bis,
                row.pause_beginn,
                row.pause_ende,
                row.pause2_beginn,
                row.pause2_ende,
            )
            if netto is not None:
                summe += netto
        return summe

    @staticmethod
    def _coerce_wochentag(value: object) -> int | None:
        if isinstance(value, int) and 1 <= value <= 7:
            return value
        if isinstance(value, str):
            text = value.strip()
            for wert, label in WOCHENTAG_LABELS:
                if text.lower() == label.lower():
                    return wert
            try:
                num = int(text)
            except ValueError:
                return None
            if 1 <= num <= 7:
                return num
        return None

    @staticmethod
    def _calculate_zuleistende_zeit(
        uhrzeit_von: str,
        uhrzeit_bis: str,
        pause_von: str,
        pause_bis: str,
        pause2_von: str = "",
        pause2_bis: str = "",
    ) -> str:
        netto = netto_arbeitsminuten(
            uhrzeit_von,
            uhrzeit_bis,
            pause_von,
            pause_bis,
            pause2_von,
            pause2_bis,
        )
        if netto is None:
            return ""
        return minuten_als_hh_mm(netto)

    @staticmethod
    def _parse_minutes(text: str) -> int | None:
        return parse_uhrzeit_minuten(text)


def _label_for_wochentag(wochentag: int) -> str:
    for wert, label in WOCHENTAG_LABELS:
        if wert == wochentag:
            return label
    return ""
