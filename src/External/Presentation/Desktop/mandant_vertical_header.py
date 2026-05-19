"""Vertikaler Tabellenkopf: Zeilennummern-Farbe je mandant_id der Zeile."""

from __future__ import annotations

from collections.abc import Sequence

from PySide6.QtCore import QAbstractTableModel, Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QHeaderView, QStyle, QStyleOptionHeader, QTableView

from App.app_config import Mandant

DEFAULT_ROWCOUNTER_COLOR = "#000000"


def mandant_rowcounter_farben(mandanten: Sequence[Mandant]) -> dict[int, str]:
    return {mandant.id: mandant.rowcounter_color for mandant in mandanten}


class MandantVerticalHeaderView(QHeaderView):
    """Zeilennummern mit Farbe aus der mandant_id der Tabellenzeile (nicht Combobox)."""

    def __init__(
        self,
        mandant_farben: dict[int, str],
        table_view: QTableView,
        parent=None,
    ) -> None:
        super().__init__(Qt.Orientation.Vertical, parent)
        self._mandant_farben = mandant_farben
        self._table_view = table_view
        self.setStyleSheet("QHeaderView::section { font-weight: bold; }")
        self._verbinde_modell_signale()

    def _verbinde_modell_signale(self) -> None:
        model = self._table_view.model()
        if model is None:
            return
        model.modelReset.connect(self._zeilenzaehler_neu_malen)
        model.dataChanged.connect(self._zeilenzaehler_neu_malen)
        model.rowsInserted.connect(self._zeilenzaehler_neu_malen)
        model.rowsRemoved.connect(self._zeilenzaehler_neu_malen)
        model.layoutChanged.connect(self._zeilenzaehler_neu_malen)

    def _zeilenzaehler_neu_malen(self, *_args) -> None:
        self.viewport().update()

    def _table_model(self) -> QAbstractTableModel | None:
        model = self._table_view.model()
        return model if isinstance(model, QAbstractTableModel) else None

    def _farbe_fuer_zeile(self, logical_index: int) -> str:
        model = self._table_model()
        if model is not None and hasattr(model, "mandant_id_for_row"):
            mandant_id = model.mandant_id_for_row(logical_index)  # type: ignore[attr-defined]
            if mandant_id is not None:
                return self._mandant_farben.get(mandant_id, DEFAULT_ROWCOUNTER_COLOR)
        return DEFAULT_ROWCOUNTER_COLOR

    def paintSection(self, painter, rect, logical_index: int) -> None:  # noqa: N802
        model = self.model()
        opt = QStyleOptionHeader()
        self.initStyleOption(opt)
        opt.rect = rect
        opt.section = logical_index
        opt.textAlignment = Qt.AlignmentFlag.AlignCenter
        if model is not None:
            text = model.headerData(
                logical_index, Qt.Orientation.Vertical, Qt.ItemDataRole.DisplayRole
            )
            opt.text = str(text) if text is not None else ""
        farbe = QColor(self._farbe_fuer_zeile(logical_index))
        opt.palette.setColor(QPalette.ColorRole.ButtonText, farbe)
        opt.palette.setColor(QPalette.ColorRole.WindowText, farbe)
        self.style().drawControl(
            QStyle.ControlElement.CE_Header, opt, painter, self
        )


def install_mandant_vertical_header(
    table: QTableView, mandanten: Sequence[Mandant]
) -> MandantVerticalHeaderView:
    """Ersetzt den vertikalen Kopf durch mandantenspezifische Zeilennummern-Farben."""
    header = MandantVerticalHeaderView(mandant_rowcounter_farben(mandanten), table, table)
    table.setVerticalHeader(header)
    if table.model() is not None:
        header.setModel(table.model())
    return header
