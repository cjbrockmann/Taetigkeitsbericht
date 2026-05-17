from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt


@dataclass
class FeiertagRow:
    datum: str
    feiertagsname: str
    ist_halber_tag: bool = False
    ist_offiziell: bool = True
    hinweis: str = ""


class FeiertagTableModel(QAbstractTableModel):
    HEADERS = ["Datum", "Feiertag", "Umfang", "Offiziell", "Hinweis"]
    HEADER_TOOLTIPS = [
        "Datum des Feiertags",
        "Bezeichnung",
        "Ganzer oder halber Feiertag",
        "Gesetzlicher/offizieller Feiertag",
        "Zusatzinfo",
    ]

    def __init__(self) -> None:
        super().__init__()
        self._rows: list[FeiertagRow] = []

    @property
    def rows(self) -> list[FeiertagRow]:
        return self._rows

    def set_rows(self, rows: list[FeiertagRow]) -> None:
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
        if role == Qt.ToolTipRole and orientation == Qt.Horizontal:
            if 0 <= section < len(self.HEADER_TOOLTIPS):
                return self.HEADER_TOOLTIPS[section]
            return None
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if 0 <= section < len(self.HEADERS):
                return self.HEADERS[section]
        if role == Qt.DisplayRole and orientation == Qt.Vertical:
            return str(section + 1)
        return None

    @staticmethod
    def _umfang_text(ist_halber_tag: bool) -> str:
        return "Halb" if ist_halber_tag else "Ganz"

    @staticmethod
    def _offiziell_text(ist_offiziell: bool) -> str:
        return "Ja" if ist_offiziell else "Nein"

    @staticmethod
    def _parse_umfang(text: str) -> bool | None:
        t = text.strip().lower()
        if t in ("halb", "h", "0.5", "halber"):
            return True
        if t in ("ganz", "g", "1", "ganzer"):
            return False
        return None

    @staticmethod
    def _parse_offiziell(text: str) -> bool | None:
        t = text.strip().lower()
        if t in ("ja", "j", "1", "true", "offiziell", "gesetzlich"):
            return True
        if t in ("nein", "n", "0", "false", "nicht offiziell"):
            return False
        return None

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> str | None:
        if not index.isValid():
            return None
        row = self._rows[index.row()]
        if role == Qt.TextAlignmentRole and index.column() in (2, 3):
            return int(Qt.AlignmentFlag.AlignCenter)
        if role not in (Qt.DisplayRole, Qt.EditRole):
            return None
        match index.column():
            case 0:
                return row.datum
            case 1:
                return row.feiertagsname
            case 2:
                return self._umfang_text(row.ist_halber_tag)
            case 3:
                return self._offiziell_text(row.ist_offiziell)
            case 4:
                return row.hinweis
            case _:
                return None

    def setData(self, index: QModelIndex, value: object, role: int = Qt.EditRole) -> bool:  # noqa: N802
        if not index.isValid() or role != Qt.EditRole:
            return False
        row = self._rows[index.row()]
        text = str(value).strip()
        if index.column() == 2:
            parsed = self._parse_umfang(text)
            if parsed is None:
                return False
            row.ist_halber_tag = parsed
        elif index.column() == 3:
            parsed = self._parse_offiziell(text)
            if parsed is None:
                return False
            row.ist_offiziell = parsed
        else:
            return False
        self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
        return True

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.ItemIsEnabled
        if index.column() in (2, 3):
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled
