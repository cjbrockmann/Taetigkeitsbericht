from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor

from External.Presentation.Desktop.dirty_row_table_mixin import DirtyRowTableModelMixin


@dataclass
class BetriebsferienRow:
    id: int | None
    datum_von: str
    datum_bis: str
    name: str
    anmerkung: str


class BetriebsferienTableModel(DirtyRowTableModelMixin, QAbstractTableModel):
    HEADERS = [
        "Von",
        "Bis",
        "Bezeichnung",
        "Anmerkung",
    ]

    def __init__(self) -> None:
        super().__init__()
        self._init_dirty_row_support()
        self._rows: list[BetriebsferienRow] = []

    @property
    def rows(self) -> list[BetriebsferienRow]:
        return self._rows

    def set_rows(self, rows: list[BetriebsferienRow]) -> None:
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
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if 0 <= section < len(self.HEADERS):
                return self.HEADERS[section]
        if role == Qt.DisplayRole and orientation == Qt.Vertical:
            return f"{section + 1:02d}"
        return None

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> str | QColor | None:
        if not index.isValid():
            return None
        if role == Qt.ItemDataRole.ForegroundRole:
            return self.foreground_color_for_index(index)
        if role not in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            return None
        row = self._rows[index.row()]
        col = index.column()
        if col == 0:
            return row.datum_von
        if col == 1:
            return row.datum_bis
        if col == 2:
            return row.name
        if col == 3:
            return row.anmerkung
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.ItemIsEnabled
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled
