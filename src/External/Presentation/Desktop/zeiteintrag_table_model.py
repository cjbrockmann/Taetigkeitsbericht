from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QPointF, Qt
from PySide6.QtGui import QBrush, QColor, QIcon, QPainter, QPen, QPixmap, QPolygonF

from Core.Domain.models.models_worktime import Feiertag
from External.Presentation.Desktop.arbeitszeit_berechnung import (
    minuten_als_hh_mm,
    netto_arbeitsminuten,
    parse_uhrzeit_minuten,
)
from External.Presentation.Desktop.stundenplan_registry import StundenplanRegistry
from External.Presentation.Desktop.table_view_styles import (
    DIRTY_ROW_TEXT_COLOR,
    NORMAL_ROW_TEXT_COLOR,
)


def feiertag_stern_icon() -> QIcon:
    if not hasattr(feiertag_stern_icon, "_cache"):
        groesse = 16
        pm = QPixmap(groesse, groesse)
        pm.fill(QColor(0, 0, 0, 0))
        maler = QPainter(pm)
        maler.setRenderHint(QPainter.RenderHint.Antialiasing)
        mitte_x = groesse / 2
        mitte_y = groesse / 2 + 0.5
        radius_aussen = 6.0
        radius_innen = 2.4
        punkte: list[QPointF] = []
        for k in range(10):
            winkel = math.pi / 2 + k * math.pi / 5
            r = radius_aussen if k % 2 == 0 else radius_innen
            punkte.append(
                QPointF(
                    mitte_x + r * math.cos(winkel),
                    mitte_y - r * math.sin(winkel),
                )
            )
        maler.setBrush(QBrush(QColor("#f9a825")))
        maler.setPen(QPen(QColor("#c17900"), 1))
        maler.drawPolygon(QPolygonF(punkte))
        maler.end()
        feiertag_stern_icon._cache = QIcon(pm)
    return feiertag_stern_icon._cache


@dataclass
class ZeiteintragRow:
    id: UUID | None = None
    datum: str = ""
    uhrzeit_von: str = ""
    uhrzeit_bis: str = ""
    pause_beginn: str = ""
    pause_ende: str = ""
    pause2_beginn: str = ""
    pause2_ende: str = ""
    anmerkung: str = ""
    geleistete_stunden: str = ""
    soll_stunden_nach_stundenplan: str = ""
    soll_stunden_nach_vertrag: str = ""
    ist_urlaub: bool = False
    ist_krank: bool = False
    ist_feiertag: bool = False
    ist_ferien: bool = False
    ist_betriebsferien: bool = False
    feiertagsname: str = ""
    schulferienname: str = ""


class ZeiteintragTableModel(QAbstractTableModel):
    _MAX_ANMERKUNG_LAENGE = 80

    HEADERS = [
        "Tag",
        "Datum",
        "Von",
        "Bis",
        "Von",
        "Bis",
        "Von",
        "Bis",
        "Geleistet",
        "Soll",
        "Vertrag",
        "Kommentar",
        "Tag",
        "Urlaub",
        "Krank",
        "Feiertag",
        "Ferien",
        "Betriebsferien",
        "Feiertagsname",
        "Schulferienname",
    ]
    HEADER_TOOLTIPS = [
        "Wird automatisch aus dem Datum ermittelt",
        "Erwartetes Format: DD.MM.YYYY, z. B. 07.05.2026",
        "Erwartetes Format: HH:MM, z. B. 08:30",
        "Erwartetes Format: HH:MM, z. B. 17:00",
        "Optionales Format: HH:MM, z. B. 12:00",
        "Optionales Format: HH:MM, z. B. 12:30",
        "Optionales Format: HH:MM, z. B. 14:00",
        "Optionales Format: HH:MM, z. B. 14:15",
        "Geleistete Zeit (Bis - Von - beide Pausen), Format HH:MM",
        "Gesamt-Soll aus Stundenplan (Wochentag), nur erste Zeile je Tag, Format HH:MM",
        "Soll nach Vertrag, Format HH:MM",
        "Freitext (max. 80 Zeichen)",
        "Kalendertag als Text fuer Excel (z. B. 7.)",
        "Tag ist Urlaub",
        "Tag ist Krankheit",
        "Tag ist Feiertag",
        "Tag ist Schulferien",
        "Tag ist Betriebsferien",
        "Name des Feiertags",
        "Name der Schulferien",
    ]

    def __init__(self) -> None:
        super().__init__()
        self._rows: list[ZeiteintragRow] = []
        self._dirty_rows: set[int] = set()
        self._feiertag_nach_datum: dict[date, Feiertag] = {}
        self._stundenplan_registry: StundenplanRegistry | None = None

    @property
    def rows(self) -> list[ZeiteintragRow]:
        return self._rows

    def set_rows(self, rows: list[ZeiteintragRow]) -> None:
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
            return self._day_of_month_from_date(self._rows[section].datum)
        if role != Qt.DisplayRole:
            return None
        return None

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> object | None:
        if not index.isValid():
            return None
        row = self._rows[index.row()]
        if role == Qt.TextAlignmentRole and index.column() in (12, 13, 14, 15, 16, 17):
            return int(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        if role == Qt.BackgroundRole:
            if self._is_weekend_date(row.datum):
                return QColor("#eeeeee")
            return QColor("#ffffff")
        if role == Qt.DecorationRole and index.column() == 0:
            if self._feiertag_fuer_datumtext(row.datum) is not None:
                return feiertag_stern_icon()
            return None
        if role == Qt.ToolTipRole:
            if index.column() == 10:
                return self.HEADER_TOOLTIPS[10]
            if index.column() in (0, 1):
                feiertag = self._feiertag_fuer_datumtext(row.datum)
                if feiertag is None:
                    return None
                tooltip = feiertag.feiertagsname
                if feiertag.hinweis:
                    tooltip = f"{tooltip}\n{feiertag.hinweis}"
                return tooltip
            return None
        if role == Qt.ForegroundRole:
            if index.row() in self._dirty_rows:
                return QColor(DIRTY_ROW_TEXT_COLOR)
            return QColor(NORMAL_ROW_TEXT_COLOR)
        if role not in (Qt.DisplayRole, Qt.EditRole):
            return None
        match index.column():
            case 0:
                return self._weekday_from_date(row.datum)
            case 1:
                return row.datum
            case 2:
                return row.uhrzeit_von
            case 3:
                return row.uhrzeit_bis
            case 4:
                return row.pause_beginn
            case 5:
                return row.pause_ende
            case 6:
                return row.pause2_beginn
            case 7:
                return row.pause2_ende
            case 8:
                return self._calculate_geleistete_zeit(
                    row.uhrzeit_von,
                    row.uhrzeit_bis,
                    row.pause_beginn,
                    row.pause_ende,
                    row.pause2_beginn,
                    row.pause2_ende,
                )
            case 9:
                return row.soll_stunden_nach_stundenplan
            case 10:
                return row.soll_stunden_nach_vertrag
            case 11:
                return row.anmerkung
            case 12:
                return self._kalendertag_mit_punkt_fuer_excel(row.datum)
            case 13:
                return "✓" if row.ist_urlaub else ""
            case 14:
                return "✓" if row.ist_krank else ""
            case 15:
                return "✓" if row.ist_feiertag else ""
            case 16:
                return "✓" if row.ist_ferien else ""
            case 17:
                return "✓" if row.ist_betriebsferien else ""
            case 18:
                return row.feiertagsname
            case 19:
                return row.schulferienname
            case _:
                return None

    def setData(self, index: QModelIndex, value: object, role: int = Qt.EditRole) -> bool:  # noqa: N802
        if not index.isValid() or role != Qt.EditRole:
            return False

        row = self._rows[index.row()]
        text = str(value)
        if index.column() != 11:
            text = text.strip()
        if index.column() == 0:
            return False
        elif index.column() == 1:
            row.datum = text
            self._trage_feiertagsname_in_leeres_kommentar_ein(row)
        elif index.column() == 2:
            row.uhrzeit_von = text
        elif index.column() == 3:
            row.uhrzeit_bis = text
        elif index.column() == 4:
            row.pause_beginn = text
        elif index.column() == 5:
            row.pause_ende = text
        elif index.column() == 6:
            row.pause2_beginn = text
        elif index.column() == 7:
            row.pause2_ende = text
        elif index.column() in (8, 9, 10, 12, 13, 14, 15, 16, 17, 18, 19):
            return False
        elif index.column() == 11:
            row.anmerkung = text
        else:
            return False

        if index.column() == 1:
            left = self.index(index.row(), 0)
            right = self.index(index.row(), len(self.HEADERS) - 1)
            self.dataChanged.emit(
                left,
                right,
                [
                    Qt.DisplayRole,
                    Qt.EditRole,
                    Qt.BackgroundRole,
                    Qt.ToolTipRole,
                    Qt.DecorationRole,
                ],
            )
            self.headerDataChanged.emit(Qt.Vertical, index.row(), index.row())
            if self._rows:
                v0 = self.index(0, 10)
                v1 = self.index(len(self._rows) - 1, 10)
                self.dataChanged.emit(v0, v1, [Qt.DisplayRole, Qt.EditRole])
            return True

        if index.column() in (2, 3, 4, 5, 6, 7):
            left = self.index(index.row(), index.column())
            right = self.index(index.row(), 9)
            self.dataChanged.emit(
                left, right, [Qt.DisplayRole, Qt.EditRole, Qt.BackgroundRole]
            )
            return True

        self.dataChanged.emit(
            index, index, [Qt.DisplayRole, Qt.EditRole, Qt.BackgroundRole]
        )
        return True

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.ItemIsEnabled
        if index.column() in (0, 8, 9, 10, 12, 13, 14, 15, 16, 17, 18, 19):
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    def add_empty_row(self, position: int | None = None, datum: str = "") -> int:
        if position is None or position < 0 or position > len(self._rows):
            position = len(self._rows)
        self.beginInsertRows(QModelIndex(), position, position)
        self._rows.insert(position, ZeiteintragRow(datum=datum))
        self.endInsertRows()
        zeile = self._rows[position]
        if self._trage_feiertagsname_in_leeres_kommentar_ein(zeile):
            idx = self.index(position, 11)
            self.dataChanged.emit(
                idx,
                idx,
                [Qt.DisplayRole, Qt.EditRole, Qt.BackgroundRole],
            )
        return position

    def remove_rows(self, row_indices: list[int]) -> None:
        for row_index in sorted(set(row_indices), reverse=True):
            if row_index < 0 or row_index >= len(self._rows):
                continue
            self.beginRemoveRows(QModelIndex(), row_index, row_index)
            del self._rows[row_index]
            self.endRemoveRows()

    def set_feiertag_nach_datum(self, mapping: dict[date, Feiertag]) -> None:
        self._feiertag_nach_datum = dict(mapping)

    def ergaenze_feiertagsname_in_leerem_kommentar(self) -> None:
        """Schreibt den Feiertagsnamen in die Kommentarspalte, wenn diese leer ist."""
        for zeilen_index, row in enumerate(self._rows):
            if not self._trage_feiertagsname_in_leeres_kommentar_ein(row):
                continue
            idx = self.index(zeilen_index, 11)
            self.dataChanged.emit(
                idx,
                idx,
                [Qt.DisplayRole, Qt.EditRole, Qt.BackgroundRole],
            )

    def set_stundenplan_registry(self, registry: StundenplanRegistry | None) -> None:
        self._stundenplan_registry = registry

    def stundenplan_soll_aktualisieren(self) -> None:
        if not self._rows:
            return
        for r in range(len(self._rows)):
            idx = self.index(r, 9)
            self.dataChanged.emit(idx, idx, [Qt.DisplayRole])

    def feiertag_darstellung_aktualisieren(self) -> None:
        if not self._rows:
            return
        top_left = self.index(0, 0)
        bottom_right = self.index(len(self._rows) - 1, len(self.HEADERS) - 1)
        self.dataChanged.emit(
            top_left,
            bottom_right,
            [Qt.DisplayRole, Qt.BackgroundRole, Qt.ToolTipRole, Qt.DecorationRole],
        )

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

    def summen_geleistet_und_soll_minuten(self) -> tuple[int, int]:
        """Summe Geleistet- und Soll-Minuten wie in den Spalten 6 und 7 angezeigt."""
        geleistet = 0
        soll = 0
        for row in self._rows:
            gz = self._calculate_geleistete_zeit(
                row.uhrzeit_von,
                row.uhrzeit_bis,
                row.pause_beginn,
                row.pause_ende,
                row.pause2_beginn,
                row.pause2_ende,
            )
            if gz:
                m = self._parse_minutes(gz)
                if m is not None:
                    geleistet += m
            sz = row.soll_stunden_nach_stundenplan
            if sz:
                m = self._parse_minutes(sz)
                if m is not None:
                    soll += m
        return geleistet, soll

    def summe_soll_nach_vertrag_minuten(self) -> int:
        """Summe Vertrags-Soll: je Kalendertag nur die erste Zeile (wie in Spalte 10)."""
        summe = 0
        for row in self._rows:
            txt = row.soll_stunden_nach_vertrag.strip() if row.soll_stunden_nach_vertrag else ""
            if not txt:
                continue
            m = self._parse_minutes(txt)
            if m is not None:
                summe += m
        return summe

    @staticmethod
    def minuten_als_hh_mm(gesamt_minuten: int) -> str:
        return minuten_als_hh_mm(gesamt_minuten)

    @staticmethod
    def _calculate_geleistete_zeit(
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

    @staticmethod
    def _weekday_from_date(datum_text: str) -> str:
        text = datum_text.strip()
        if not text:
            return ""
        try:
            datum = datetime.strptime(text, "%d.%m.%Y").date()
        except ValueError:
            return ""
        return ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"][datum.weekday()]

    @staticmethod
    def _day_of_month_from_date(datum_text: str) -> str:
        text = datum_text.strip()
        if not text:
            return ""
        try:
            datum = datetime.strptime(text, "%d.%m.%Y").date()
        except ValueError:
            return ""
        return f"{datum.day:02d}"

    @staticmethod
    def _kalendertag_mit_punkt_fuer_excel(datum_text: str) -> str | None:
        """z. B. '7.' damit Excel den Wert als Text (nicht als Zahl) behandelt."""
        text = datum_text.strip()
        if not text:
            return None
        try:
            datum = datetime.strptime(text, "%d.%m.%Y").date()
        except ValueError:
            return None
        return f"{datum.day}."

    def _feiertag_fuer_datumtext(self, datum_text: str) -> Feiertag | None:
        text = datum_text.strip()
        if not text:
            return None
        try:
            d = datetime.strptime(text, "%d.%m.%Y").date()
        except ValueError:
            return None
        return self._feiertag_nach_datum.get(d)

    def _trage_feiertagsname_in_leeres_kommentar_ein(self, row: ZeiteintragRow) -> bool:
        if row.anmerkung.strip():
            return False
        feiertag = self._feiertag_fuer_datumtext(row.datum)
        if feiertag is None:
            return False
        name = feiertag.feiertagsname.strip()
        if not name:
            return False
        row.anmerkung = name[: self._MAX_ANMERKUNG_LAENGE]
        return True

    def ist_feiertag(self, datum_text: str) -> bool:
        return self._feiertag_fuer_datumtext(datum_text) is not None

    @staticmethod
    def _is_weekend_date(datum_text: str) -> bool:
        text = datum_text.strip()
        if not text:
            return False
        try:
            datum = datetime.strptime(text, "%d.%m.%Y").date()
        except ValueError:
            return False
        return datum.weekday() >= 5
