from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QPointF, Qt, QRect
from PySide6.QtGui import QBrush, QColor, QFont, QIcon, QPainter, QPen, QPixmap, QPolygonF


class ZeiteintragSpalte:
    TAG = 0
    DATUM = 1
    FEIERTAG_KZ = 2
    URLAUB = 3
    KRANK = 4
    FERIEN = 5
    BETRIEBSFERIEN = 6
    VON = 7
    BIS = 8
    PAUSE1_VON = 9
    PAUSE1_BIS = 10
    PAUSE2_VON = 11
    PAUSE2_BIS = 12
    GELEISTET = 13
    SOLL = 14
    VERTRAG = 15
    KOMMENTAR = 16
    TAG_EXCEL = 17
    FEIERTAGSNAME = 18
    SCHULFERIENNAME = 19

    STATUS_KENNZEICHEN = frozenset(
        {URLAUB, KRANK, FEIERTAG_KZ, FERIEN, BETRIEBSFERIEN}
    )
    ZEITFELDER = frozenset({VON, BIS, PAUSE1_VON, PAUSE1_BIS, PAUSE2_VON, PAUSE2_BIS})

    STATUS_SPALTE_BREITE = 28
    ZEIT_SPALTE_BREITE = 50
    STATUS_ICON_RAND = 5
    STATUS_ICON_MAX_GROESSE = 16
    KOMMENTAR_MIN_BREITE = 200
    NAME_SPALTE_BREITE = 120


_KENNZEICHEN_ICON_CACHE: dict[str, QIcon] = {}


def _rundes_kennzeichen_icon(letter: str, hintergrund: str, vordergrund: str = "#ffffff") -> QIcon:
    groesse = ZeiteintragSpalte.STATUS_ICON_MAX_GROESSE
    schluessel = f"{letter}:{hintergrund}:{vordergrund}:{groesse}"
    if schluessel in _KENNZEICHEN_ICON_CACHE:
        return _KENNZEICHEN_ICON_CACHE[schluessel]
    pm = QPixmap(groesse, groesse)
    pm.fill(QColor(0, 0, 0, 0))
    maler = QPainter(pm)
    maler.setRenderHint(QPainter.RenderHint.Antialiasing)
    maler.setBrush(QBrush(QColor(hintergrund)))
    maler.setPen(Qt.PenStyle.NoPen)
    maler.drawEllipse(1, 1, groesse - 2, groesse - 2)
    font = QFont()
    font.setBold(True)
    font.setPixelSize(10)
    maler.setFont(font)
    maler.setPen(QPen(QColor(vordergrund)))
    maler.drawText(QRect(0, 0, groesse, groesse), Qt.AlignmentFlag.AlignCenter, letter)
    maler.end()
    icon = QIcon(pm)
    _KENNZEICHEN_ICON_CACHE[schluessel] = icon
    return icon


def urlaub_kennzeichen_icon() -> QIcon:
    return _rundes_kennzeichen_icon("U", "#2e7d32")


def krank_kennzeichen_icon() -> QIcon:
    return _rundes_kennzeichen_icon("K", "#c62828")


def ferien_kennzeichen_icon() -> QIcon:
    return _rundes_kennzeichen_icon("S", "#1565c0")


def betriebsferien_kennzeichen_icon() -> QIcon:
    return _rundes_kennzeichen_icon("B", "#7b1fa2")

from Core.Domain.models.models_worktime import Feiertag
from External.Presentation.Desktop.arbeitszeit_berechnung import (
    minuten_als_hh_mm,
    parse_uhrzeit_minuten,
)
from External.Presentation.Desktop.stundenplan_registry import StundenplanRegistry
from External.Presentation.Desktop.table_view_styles import (
    DIRTY_ROW_TEXT_COLOR,
    NORMAL_ROW_TEXT_COLOR,
)

# Gleicher Grauton wie Wochenendzeilen (siehe data(), Qt.BackgroundRole).
ZEITEINTRAG_WOCHENENDE_HINTERGRUND = QColor("#eeeeee")
ZEITEINTRAG_NORMALER_HINTERGRUND = QColor("#ffffff")


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
        "F",
        "U",
        "K",
        "Sf",
        "Bf",
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
        "Feiertagsname",
        "Schulferienname",
    ]
    HEADER_TOOLTIPS = [
        "Wird automatisch aus dem Datum ermittelt",
        "Erwartetes Format: DD.MM.YYYY, z. B. 07.05.2026",
        "Feiertag — Kennzeichen an gesetzlichen Feiertagen",
        "Urlaub — Kennzeichen, wenn der Tag ein Urlaubstag ist",
        "Krankheit — Kennzeichen, wenn der Tag ein Krankheitstag ist",
        "Schulferien — Kennzeichen während Schulferien",
        "Betriebsferien — Kennzeichen während Betriebsferien",
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
        "Kalendertag als Text für Excel (z. B. 7.)",
        "Name des Feiertags",
        "Name der Schulferien",
    ]

    def __init__(
        self, grauer_hintergrund_spalten: Sequence[int] | None = None
    ) -> None:
        super().__init__()
        self._rows: list[ZeiteintragRow] = []
        self._dirty_rows: set[int] = set()
        self._feiertag_nach_datum: dict[date, Feiertag] = {}
        self._stundenplan_registry: StundenplanRegistry | None = None
        self._grauer_hintergrund_spalten = frozenset(grauer_hintergrund_spalten or ())

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
        col = index.column()
        if role == Qt.TextAlignmentRole and col in ZeiteintragSpalte.STATUS_KENNZEICHEN | {
            ZeiteintragSpalte.TAG_EXCEL
        }:
            return int(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        if role == Qt.BackgroundRole:
            if self._is_weekend_date(row.datum):
                return ZEITEINTRAG_WOCHENENDE_HINTERGRUND
            if col in self._grauer_hintergrund_spalten:
                return ZEITEINTRAG_WOCHENENDE_HINTERGRUND
            return ZEITEINTRAG_NORMALER_HINTERGRUND
        if role == Qt.DecorationRole:
            if col == ZeiteintragSpalte.TAG:
                if self._feiertag_fuer_datumtext(row.datum) is not None:
                    return feiertag_stern_icon()
                return None
            if col == ZeiteintragSpalte.URLAUB and row.ist_urlaub:
                return urlaub_kennzeichen_icon()
            if col == ZeiteintragSpalte.KRANK and row.ist_krank:
                return krank_kennzeichen_icon()
            if col == ZeiteintragSpalte.FEIERTAG_KZ and row.ist_feiertag:
                return feiertag_stern_icon()
            if col == ZeiteintragSpalte.FERIEN and row.ist_ferien:
                return ferien_kennzeichen_icon()
            if col == ZeiteintragSpalte.BETRIEBSFERIEN and row.ist_betriebsferien:
                return betriebsferien_kennzeichen_icon()
            return None
        if role == Qt.ToolTipRole:
            if col == ZeiteintragSpalte.VERTRAG:
                return self.HEADER_TOOLTIPS[ZeiteintragSpalte.VERTRAG]
            if col in ZeiteintragSpalte.STATUS_KENNZEICHEN:
                if not self._kennzeichen_icon_aktiv(row, col):
                    return None
                if col == ZeiteintragSpalte.FEIERTAG_KZ:
                    name = row.feiertagsname.strip()
                    feiertag = self._feiertag_fuer_datumtext(row.datum)
                    if not name and feiertag is not None:
                        name = feiertag.feiertagsname.strip()
                    if not name:
                        return None
                    tooltip = name
                    if feiertag is not None and feiertag.hinweis:
                        tooltip = f"{tooltip}\n{feiertag.hinweis}"
                    return tooltip
                if col == ZeiteintragSpalte.FERIEN:
                    name = row.schulferienname.strip()
                    return name or None
                return self.HEADER_TOOLTIPS[col]
            if col in (ZeiteintragSpalte.TAG, ZeiteintragSpalte.DATUM):
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
        if col in ZeiteintragSpalte.STATUS_KENNZEICHEN:
            return ""
        match col:
            case ZeiteintragSpalte.TAG:
                return self._weekday_from_date(row.datum)
            case ZeiteintragSpalte.DATUM:
                return row.datum
            case ZeiteintragSpalte.VON:
                return row.uhrzeit_von
            case ZeiteintragSpalte.BIS:
                return row.uhrzeit_bis
            case ZeiteintragSpalte.PAUSE1_VON:
                return row.pause_beginn
            case ZeiteintragSpalte.PAUSE1_BIS:
                return row.pause_ende
            case ZeiteintragSpalte.PAUSE2_VON:
                return row.pause2_beginn
            case ZeiteintragSpalte.PAUSE2_BIS:
                return row.pause2_ende
            case ZeiteintragSpalte.GELEISTET:
                return row.geleistete_stunden
            case ZeiteintragSpalte.SOLL:
                return row.soll_stunden_nach_stundenplan
            case ZeiteintragSpalte.VERTRAG:
                return row.soll_stunden_nach_vertrag
            case ZeiteintragSpalte.KOMMENTAR:
                return row.anmerkung
            case ZeiteintragSpalte.TAG_EXCEL:
                return self._kalendertag_mit_punkt_fuer_excel(row.datum)
            case ZeiteintragSpalte.FEIERTAGSNAME:
                return row.feiertagsname
            case ZeiteintragSpalte.SCHULFERIENNAME:
                return row.schulferienname
            case _:
                return None

    def setData(self, index: QModelIndex, value: object, role: int = Qt.EditRole) -> bool:  # noqa: N802
        if not index.isValid() or role != Qt.EditRole:
            return False

        row = self._rows[index.row()]
        text = str(value)
        col = index.column()
        if col != ZeiteintragSpalte.KOMMENTAR:
            text = text.strip()
        if col == ZeiteintragSpalte.TAG:
            return False
        elif col == ZeiteintragSpalte.DATUM:
            row.datum = text
        elif col == ZeiteintragSpalte.VON:
            row.uhrzeit_von = text
        elif col == ZeiteintragSpalte.BIS:
            row.uhrzeit_bis = text
        elif col == ZeiteintragSpalte.PAUSE1_VON:
            row.pause_beginn = text
        elif col == ZeiteintragSpalte.PAUSE1_BIS:
            row.pause_ende = text
        elif col == ZeiteintragSpalte.PAUSE2_VON:
            row.pause2_beginn = text
        elif col == ZeiteintragSpalte.PAUSE2_BIS:
            row.pause2_ende = text
        elif col in (
            ZeiteintragSpalte.STATUS_KENNZEICHEN
            | {
                ZeiteintragSpalte.GELEISTET,
                ZeiteintragSpalte.SOLL,
                ZeiteintragSpalte.VERTRAG,
                ZeiteintragSpalte.TAG_EXCEL,
                ZeiteintragSpalte.FEIERTAGSNAME,
                ZeiteintragSpalte.SCHULFERIENNAME,
            }
        ):
            return False
        elif col == ZeiteintragSpalte.KOMMENTAR:
            row.anmerkung = text
        else:
            return False

        if col == ZeiteintragSpalte.DATUM:
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
                v0 = self.index(0, ZeiteintragSpalte.VERTRAG)
                v1 = self.index(len(self._rows) - 1, ZeiteintragSpalte.VERTRAG)
                self.dataChanged.emit(v0, v1, [Qt.DisplayRole, Qt.EditRole])
            return True

        if col in ZeiteintragSpalte.ZEITFELDER:
            left = self.index(index.row(), col)
            right = self.index(index.row(), ZeiteintragSpalte.SOLL)
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
        col = index.column()
        if col in (
            {ZeiteintragSpalte.TAG}
            | ZeiteintragSpalte.STATUS_KENNZEICHEN
            | {
                ZeiteintragSpalte.GELEISTET,
                ZeiteintragSpalte.SOLL,
                ZeiteintragSpalte.VERTRAG,
                ZeiteintragSpalte.TAG_EXCEL,
                ZeiteintragSpalte.FEIERTAGSNAME,
                ZeiteintragSpalte.SCHULFERIENNAME,
            }
        ):
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    def add_empty_row(self, position: int | None = None, datum: str = "") -> int:
        if position is None or position < 0 or position > len(self._rows):
            position = len(self._rows)
        self.beginInsertRows(QModelIndex(), position, position)
        self._rows.insert(position, ZeiteintragRow(datum=datum))
        self.endInsertRows()
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

    def set_stundenplan_registry(self, registry: StundenplanRegistry | None) -> None:
        self._stundenplan_registry = registry

    def stundenplan_soll_aktualisieren(self) -> None:
        if not self._rows:
            return
        for r in range(len(self._rows)):
            idx = self.index(r, ZeiteintragSpalte.SOLL)
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
            gz = row.geleistete_stunden.strip()
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

    @staticmethod
    def _kennzeichen_icon_aktiv(row: ZeiteintragRow, col: int) -> bool:
        """True genau dann, wenn in der Zelle ein Status-Icon gezeichnet wird."""
        match col:
            case ZeiteintragSpalte.URLAUB:
                return row.ist_urlaub
            case ZeiteintragSpalte.KRANK:
                return row.ist_krank
            case ZeiteintragSpalte.FEIERTAG_KZ:
                return row.ist_feiertag
            case ZeiteintragSpalte.FERIEN:
                return row.ist_ferien
            case ZeiteintragSpalte.BETRIEBSFERIEN:
                return row.ist_betriebsferien
            case _:
                return False

    def _feiertag_fuer_datumtext(self, datum_text: str) -> Feiertag | None:
        text = datum_text.strip()
        if not text:
            return None
        try:
            d = datetime.strptime(text, "%d.%m.%Y").date()
        except ValueError:
            return None
        return self._feiertag_nach_datum.get(d)

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
