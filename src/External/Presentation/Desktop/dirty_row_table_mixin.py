"""Gemeinsame Unterstuetzung fuer ungespeicherte Tabellenzeilen (rote Schrift)."""

from __future__ import annotations

from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtGui import QColor

from External.Presentation.Desktop.table_view_styles import (
    DIRTY_ROW_TEXT_COLOR,
    NORMAL_ROW_TEXT_COLOR,
)


class DirtyRowTableModelMixin:
    """Mixin fuer QAbstractTableModel: _dirty_rows, set_dirty_rows, is_row_dirty."""

    _dirty_rows: set[int]

    def _init_dirty_row_support(self) -> None:
        self._dirty_rows = set()

    def set_dirty_rows(self, dirty_rows: set[int]) -> None:
        if self._dirty_rows == dirty_rows:
            return
        self._dirty_rows = set(dirty_rows)
        self.repaint_dirty_rows()

    def repaint_dirty_rows(self) -> None:
        rows = getattr(self, "_rows", None)
        if not rows:
            return
        top_left = self.index(0, 0)  # type: ignore[attr-defined]
        bottom_right = self.index(len(rows) - 1, self.columnCount() - 1)  # type: ignore[attr-defined]
        self.dataChanged.emit(top_left, bottom_right, [Qt.ItemDataRole.ForegroundRole])  # type: ignore[attr-defined]

    def is_row_dirty(self, row_index: int) -> bool:
        return row_index in self._dirty_rows

    @property
    def has_dirty_rows(self) -> bool:
        return bool(self._dirty_rows)

    def foreground_color_for_index(self, index: QModelIndex) -> QColor:
        if index.row() in self._dirty_rows:
            return QColor(DIRTY_ROW_TEXT_COLOR)
        return QColor(NORMAL_ROW_TEXT_COLOR)
