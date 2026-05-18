"""Gemeinsames QTableView-Stylesheet und Hilfen fuer ungespeicherte Zeilen (rote Schrift)."""

from __future__ import annotations

from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import (
    QHeaderView,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTabWidget,
    QTableView,
)

DIRTY_ROW_TEXT_COLOR = "#c62828"
NORMAL_ROW_TEXT_COLOR = "#000000"

# Kein erzwungenes color bei :selected, damit Delegate/Modell die Schriftfarbe setzen koennen
# (ungespeicherte Zeilen rot, auch wenn markiert).
STANDARD_TABLE_VIEW_STYLESHEET = (
    "QTableView QHeaderView::section {"
    "font-weight: bold;"
    "}"
    "QTableView::item:hover:!selected {"
    "background-color: #ececec;"
    "}"
    "QTableView::item:selected:hover {"
    "background-color: #fff9c4;"
    "}"
    "QTableView::item:selected {"
    "background-color: #fff9c4;"
    "}"
    "QTableView::item:selected:!active {"
    "background-color: #fff9c4;"
    "}"
)

ZEITEINTRAG_TABLE_VIEW_STYLESHEET = STANDARD_TABLE_VIEW_STYLESHEET

TAB_WIDGET_STYLESHEET = (
    "QTabBar::tab {"
    "color: #141414;"
    "font-weight: 600;"
    "}"
    "QTabBar::tab:selected {"
    "color: #000000;"
    "font-weight: 700;"
    "}"
)


def apply_rowcounter_color_to_vertical_header(
    vertical_header: QHeaderView, color: str
) -> None:
    """Schriftfarbe der Zeilennummern (vertikaler Tabellenkopf)."""
    vertical_header.setStyleSheet(
        f"QHeaderView::section {{ color: {color}; font-weight: bold; }}"
    )


def apply_rowcounter_color_to_table(table: QTableView, color: str) -> None:
    apply_rowcounter_color_to_vertical_header(table.verticalHeader(), color)


def style_tab_widget(tab_widget: QTabWidget) -> None:
    """Tab-Leiste: markantere und etwas groessere Beschriftung (Rahmen vom Systemstil)."""
    tab_widget.setStyleSheet(TAB_WIDGET_STYLESHEET)
    tab_bar = tab_widget.tabBar()
    font = QFont(tab_bar.font())
    point_size = font.pointSize()
    if point_size > 0:
        font.setPointSize(point_size + 1)
    else:
        font.setPixelSize(max(1, int(font.pixelSize() * 1.08)))
    font.setWeight(QFont.Weight.DemiBold)
    tab_bar.setFont(font)


def paint_option_mit_zeilenfarbe(
    option: QStyleOptionViewItem, is_dirty: bool
) -> QStyleOptionViewItem:
    """Textfarbe fuer normale und selektierte Zellen (HighlightedText)."""
    paint_option = type(option)(option)
    farbe = QColor(DIRTY_ROW_TEXT_COLOR if is_dirty else NORMAL_ROW_TEXT_COLOR)
    paint_option.palette.setColor(QPalette.ColorRole.Text, farbe)
    paint_option.palette.setColor(QPalette.ColorRole.HighlightedText, farbe)
    return paint_option


class DirtyRowItemDelegate(QStyledItemDelegate):
    """Item-Delegate: ungespeicherte Zeilen rot, auch bei Selektion."""

    def paint(self, painter, option, index):  # noqa: N802
        model = index.model()
        is_dirty = (
            model is not None
            and hasattr(model, "is_row_dirty")
            and model.is_row_dirty(index.row())
        )
        super().paint(
            painter,
            paint_option_mit_zeilenfarbe(option, is_dirty),
            index,
        )


class FeiertagItemDelegate(QStyledItemDelegate):
    """Feiertag-Tabelle: markierte Zeilen immer schwarze Schrift, Hintergrund unveraendert."""

    def paint(self, painter, option, index):  # noqa: N802
        super().paint(
            painter,
            paint_option_mit_zeilenfarbe(option, is_dirty=False),
            index,
        )
