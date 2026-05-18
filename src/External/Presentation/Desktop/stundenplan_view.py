from __future__ import annotations

from collections.abc import Sequence

from PySide6.QtCore import QPersistentModelIndex, QRect, QSize, Qt
from PySide6.QtGui import QGuiApplication, QKeySequence, QPalette, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStyle,
    QStyleOptionHeader,
    QStyledItemDelegate,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from External.Presentation.Desktop.arbeitszeit_berechnung import minuten_als_hh_mm
from External.Presentation.Desktop.stundenplan_table_model import (
    WOCHENTAG_LABELS,
    StundenplanRow,
)
from External.Presentation.Desktop.hilfe import ViewMarkdownHilfe
from External.Presentation.Desktop.message_boxes import warnung
from External.Presentation.Desktop.stundenplan_view_model import StundenplanViewModel
from External.Presentation.Desktop.table_view_styles import (
    apply_rowcounter_color_to_table,
    DirtyRowItemDelegate,
    STANDARD_TABLE_VIEW_STYLESHEET,
)


class StundenplanLiveCommitDelegate(DirtyRowItemDelegate):
    def createEditor(self, parent, option, index):  # noqa: N802
        editor = super().createEditor(parent, option, index)
        if isinstance(editor, QLineEdit):
            persistent = QPersistentModelIndex(index)

            def on_editing_finished() -> None:
                if not persistent.isValid():
                    return
                model = persistent.model()
                if model is None:
                    return
                idx = model.index(
                    persistent.row(),
                    persistent.column(),
                    persistent.parent(),
                )
                if not idx.isValid():
                    return
                editor.setProperty("_live_commit", True)
                self.setModelData(editor, model, idx)
                editor.setProperty("_live_commit", False)

            editor.editingFinished.connect(on_editing_finished)
        return editor

    def setModelData(self, editor, model, index):  # noqa: N802
        if isinstance(editor, QLineEdit):
            text = editor.text()
            if index.column() != 8:
                text = text.strip()
            is_live_commit = bool(editor.property("_live_commit"))
            if not is_live_commit and index.column() in (1, 2, 3, 4, 5, 6) and text.isdigit():
                hour = int(text)
                if 0 <= hour <= 23:
                    text = f"{hour:02d}:00"
            model.setData(index, text)
            return
        super().setModelData(editor, model, index)


class WochentagDelegate(StundenplanLiveCommitDelegate):
    def createEditor(self, parent, option, index):  # noqa: N802
        editor = QComboBox(parent)
        for wert, label in WOCHENTAG_LABELS:
            editor.addItem(label, wert)
        return editor

    def setEditorData(self, editor, index):  # noqa: N802
        if not isinstance(editor, QComboBox):
            super().setEditorData(editor, index)
            return
        current_value = index.data(Qt.EditRole)
        for combo_index in range(editor.count()):
            if editor.itemData(combo_index) == current_value:
                editor.setCurrentIndex(combo_index)
                return
        editor.setCurrentIndex(0)

    def setModelData(self, editor, model, index):  # noqa: N802
        if isinstance(editor, QComboBox):
            model.setData(index, editor.currentData())
            return
        super().setModelData(editor, model, index)


class GruppenHeaderView(QHeaderView):
    def __init__(self, orientation: Qt.Orientation, parent=None) -> None:
        super().__init__(orientation, parent)
        self._gruppen = [
            ("Arbeitsphase", 1, 2),
            ("Pause", 3, 4),
            ("Pause 2", 5, 6),
        ]
        self.setDefaultAlignment(Qt.AlignCenter)
        kopf_schrift = self.font()
        kopf_schrift.setBold(True)
        self.setFont(kopf_schrift)

    def sectionSizeFromContents(self, logical_index: int) -> QSize:  # noqa: N802
        groesse = super().sectionSizeFromContents(logical_index)
        groesse.setHeight(max(groesse.height() * 2, 44))
        return groesse

    def paintSection(self, painter, rect: QRect, logical_index: int) -> None:  # noqa: N802
        if not rect.isValid():
            return
        model = self.model()
        if model is None:
            super().paintSection(painter, rect, logical_index)
            return

        top_hoehe = rect.height() // 2
        top_rect = QRect(rect.left(), rect.top(), rect.width(), top_hoehe)
        bottom_rect = QRect(rect.left(), rect.top() + top_hoehe, rect.width(), rect.height() - top_hoehe)

        bottom_option = QStyleOptionHeader()
        self.initStyleOption(bottom_option)
        bottom_option.rect = bottom_rect
        bottom_option.section = logical_index
        bottom_option.text = str(model.headerData(logical_index, Qt.Horizontal, Qt.DisplayRole) or "")
        self.style().drawControl(QStyle.ControlElement.CE_Header, bottom_option, painter, self)

        gruppe = next((g for g in self._gruppen if g[1] <= logical_index <= g[2]), None)
        if gruppe is None:
            top_option = QStyleOptionHeader()
            self.initStyleOption(top_option)
            top_option.rect = top_rect
            top_option.section = logical_index
            top_option.text = ""
            self.style().drawControl(QStyle.ControlElement.CE_Header, top_option, painter, self)
            return

        label, start, ende = gruppe
        if logical_index != start:
            return

        span_links = self.sectionViewportPosition(start)
        span_breite = sum(self.sectionSize(col) for col in range(start, ende + 1))
        gruppen_rect = QRect(span_links, rect.top(), span_breite, top_hoehe)

        top_option = QStyleOptionHeader()
        self.initStyleOption(top_option)
        top_option.rect = gruppen_rect
        top_option.section = logical_index
        top_option.text = label
        self.style().drawControl(QStyle.ControlElement.CE_Header, top_option, painter, self)


class StundenplanView(QWidget):
    def __init__(
        self,
        view_model: StundenplanViewModel,
        parent: QWidget | None = None,
        ausgeblendete_spalten: Sequence[int] | None = None,
    ) -> None:
        super().__init__(parent)
        self._view_model = view_model
        self._ausgeblendete_spalten = tuple(ausgeblendete_spalten or ())
        self._has_unsaved_changes = False
        self._suspend_dirty_tracking = False
        self._baseline_rows: list[tuple[object, int, str, str, str, str, str, str, str]] = []
        self._build_ui()
        self._bind_view_model()

    @property
    def has_unsaved_changes(self) -> bool:
        return self._has_unsaved_changes

    def set_rowcounter_color(self, color: str) -> None:
        apply_rowcounter_color_to_table(self._table, color)

    def set_mandant_id(self, mandant_id: int) -> None:
        self._view_model.set_mandant_id(mandant_id)

    def bei_mandant_gewechselt(self) -> None:
        self._lade_alle()

    def verwerfe_ungespeicherte_aenderungen(self) -> None:
        self._lade_alle()

    def zeilen_fuer_wochentag(self, wochentag: int) -> list[StundenplanRow]:
        return [
            row
            for row in self._view_model.table_model.rows
            if row.wochentag == wochentag and (row.uhrzeit_von.strip() or row.uhrzeit_bis.strip())
        ]

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        toolbar_layout = QHBoxLayout()

        self._zeile_hinzufuegen_button = QPushButton("Zeile hinzufügen", self)
        self._zeile_loeschen_button = QPushButton("Markierte Zeile(n) löschen", self)
        self._speichern_button = QPushButton("Alle Zeilen speichern", self)
        self._status_label = QLabel("Bereit.", self)
        self._summen_label = QLabel("", self)
        self._markdown_hilfe = ViewMarkdownHilfe(
            self,
            hilfedatei="stundenplan.md",
            tooltip="Hilfe zum Stundenplan anzeigen",
            fenster_titel="Hilfe – Stundenplan",
        )

        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self._zeile_hinzufuegen_button)
        toolbar_layout.addWidget(self._zeile_loeschen_button)
        toolbar_layout.addWidget(self._speichern_button)

        self._table = QTableView(self)
        self._table.setModel(self._view_model.table_model)
        self._table.setHorizontalHeader(GruppenHeaderView(Qt.Horizontal, self._table))
        live_delegate = StundenplanLiveCommitDelegate(self._table)
        self._table.setItemDelegate(live_delegate)
        self._table.setItemDelegateForColumn(0, WochentagDelegate(self._table))
        self._table.setAlternatingRowColors(True)
        self._table.setShowGrid(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._table.setStyleSheet(STANDARD_TABLE_VIEW_STYLESHEET)
        horizontal_header = self._table.horizontalHeader()
        horizontal_header.setStretchLastSection(True)
        horizontal_header.resizeSection(0, 70)
        horizontal_header.resizeSection(3, 60)
        horizontal_header.resizeSection(4, 60)
        horizontal_header.resizeSection(5, 60)
        horizontal_header.resizeSection(6, 60)
        horizontal_header.resizeSection(7, 80)
        for spalte in self._ausgeblendete_spalten:
            self._table.setColumnHidden(spalte, True)
        self._table.verticalHeader().setVisible(True)

        root_layout.addLayout(toolbar_layout)
        root_layout.addWidget(self._table)
        fuss_layout = QHBoxLayout()
        fuss_layout.addWidget(self._status_label, 1)
        fuss_layout.addWidget(self._summen_label)
        fuss_layout.addWidget(self._markdown_hilfe.button)
        root_layout.addLayout(fuss_layout)

        self._zeile_hinzufuegen_button.clicked.connect(self._on_zeile_hinzufuegen)
        self._zeile_loeschen_button.clicked.connect(self._on_zeile_loeschen)
        self._speichern_button.clicked.connect(self._on_speichern)

        copy_shortcut = QShortcut(QKeySequence.Copy, self._table)
        copy_shortcut.setContext(Qt.WidgetWithChildrenShortcut)
        copy_shortcut.activated.connect(self._kopiere_markierte_zellen_in_zwischenablage)
        selection_model = self._table.selectionModel()
        if selection_model is not None:
            selection_model.selectionChanged.connect(self._on_selection_changed)

    def _bind_view_model(self) -> None:
        self._view_model.status_changed.connect(self._status_label.setText)
        self._view_model.error_occurred.connect(self._show_error)
        model = self._view_model.table_model
        model.dataChanged.connect(self._on_model_mutated)
        model.rowsInserted.connect(self._on_model_mutated)
        model.rowsRemoved.connect(self._on_model_mutated)
        model.modelReset.connect(self._on_model_mutated)
        model.dataChanged.connect(self._auf_stundenplan_tabelle_inhalt)
        model.rowsInserted.connect(self._auf_stundenplan_tabelle_inhalt)
        model.rowsRemoved.connect(self._auf_stundenplan_tabelle_inhalt)
        self._aktualisiere_summen_anzeige()

    def _aktualisiere_summen_anzeige(self) -> None:
        summe_min = self._view_model.table_model.summe_zuleistende_minuten()
        txt = minuten_als_hh_mm(summe_min)
        self._summen_label.setText(f"Soll: {txt}")

    def _lade_alle(self) -> None:
        self._suspend_dirty_tracking = True
        try:
            self._view_model.lade_alle()
        finally:
            self._suspend_dirty_tracking = False
        self._capture_baseline()
        self._has_unsaved_changes = False
        self._view_model.table_model.set_dirty_rows(set())

    def _on_zeile_hinzufuegen(self) -> None:
        selection_model = self._table.selectionModel()
        position: int | None = None
        wochentag = 1
        model_rows = self._view_model.table_model.rows
        if selection_model is not None:
            selected_rows = sorted({index.row() for index in selection_model.selectedRows()})
            if not selected_rows:
                current_index = selection_model.currentIndex()
                if current_index.isValid():
                    selected_rows = [current_index.row()]
            if selected_rows:
                anchor_row = selected_rows[-1]
                position = anchor_row + 1
                if 0 <= anchor_row < len(model_rows):
                    wochentag = self._naechster_wochentag(model_rows[anchor_row].wochentag)
        if position is None and model_rows:
            wochentag = self._naechster_wochentag(model_rows[-1].wochentag)

        new_row_index = self._view_model.add_row(position=position, wochentag=wochentag)

        if selection_model is not None:
            new_index = self._view_model.table_model.index(new_row_index, 1)
            selection_model.clearSelection()
            self._table.setCurrentIndex(new_index)
            self._table.scrollTo(new_index)

    @staticmethod
    def _naechster_wochentag(aktueller_wochentag: int) -> int:
        if not 1 <= aktueller_wochentag <= 7:
            return 1
        return aktueller_wochentag % 7 + 1

    def _on_zeile_loeschen(self) -> None:
        selection_model = self._table.selectionModel()
        if selection_model is None:
            return
        row_indices = [
            index.row()
            for index in selection_model.selectedRows()
            if selection_model.isRowSelected(index.row(), index.parent())
        ]
        if not row_indices:
            return
        self._view_model.remove_rows(row_indices)
        selection_model.clearSelection()

    def _on_speichern(self) -> None:
        if not self._view_model.speichere_alle():
            return
        self._lade_alle()

    def _show_error(self, message: str) -> None:
        warnung(self, "Fehler beim Speichern/Laden", message)

    def _on_model_mutated(self, *_args) -> None:
        self._aktualisiere_summen_anzeige()
        if self._suspend_dirty_tracking:
            return
        self._update_dirty_state()

    def _auf_stundenplan_tabelle_inhalt(self, *_args) -> None:
        if self._suspend_dirty_tracking:
            return
        self._view_model.synchronisiere_registry_mit_tabelle()

    def _capture_baseline(self) -> None:
        self._baseline_rows = self._current_rows_snapshot()

    def _current_rows_snapshot(self) -> list[tuple[object, int, str, str, str, str, str, str, str]]:
        snapshot: list[tuple[object, int, str, str, str, str, str, str, str]] = []
        for row in self._view_model.table_model.rows:
            uhrzeit_von = row.uhrzeit_von.strip()
            uhrzeit_bis = row.uhrzeit_bis.strip()
            if not (uhrzeit_von or uhrzeit_bis):
                continue
            snapshot.append(
                (
                    row.id,
                    row.wochentag,
                    uhrzeit_von,
                    uhrzeit_bis,
                    row.pause_beginn.strip(),
                    row.pause_ende.strip(),
                    row.pause2_beginn.strip(),
                    row.pause2_ende.strip(),
                    row.anmerkung.strip(),
                )
            )
        return snapshot

    def _update_dirty_state(self) -> None:
        current_snapshot = self._current_rows_snapshot()
        self._has_unsaved_changes = (
            current_snapshot != self._baseline_rows
            or bool(self._view_model.zu_loeschende_ids)
        )
        self._view_model.table_model.set_dirty_rows(self._compute_dirty_row_indices())

    def _compute_dirty_row_indices(self) -> set[int]:
        baseline_by_id: dict[int, tuple[int, str, str, str, str, str, str, str]] = {
            row_id: (
                wochentag,
                uhrzeit_von,
                uhrzeit_bis,
                pause_von,
                pause_bis,
                pause2_von,
                pause2_bis,
                anmerkung,
            )
            for (
                row_id,
                wochentag,
                uhrzeit_von,
                uhrzeit_bis,
                pause_von,
                pause_bis,
                pause2_von,
                pause2_bis,
                anmerkung,
            ) in self._baseline_rows
            if isinstance(row_id, int)
        }
        dirty_rows: set[int] = set()
        for index, row in enumerate(self._view_model.table_model.rows):
            uhrzeit_von = row.uhrzeit_von.strip()
            uhrzeit_bis = row.uhrzeit_bis.strip()
            if not uhrzeit_von:
                continue
            if row.id is None:
                dirty_rows.add(index)
                continue
            baseline_values = baseline_by_id.get(row.id)
            current_values = (
                row.wochentag,
                uhrzeit_von,
                uhrzeit_bis,
                row.pause_beginn.strip(),
                row.pause_ende.strip(),
                row.pause2_beginn.strip(),
                row.pause2_ende.strip(),
                row.anmerkung.strip(),
            )
            if baseline_values != current_values:
                dirty_rows.add(index)
        return dirty_rows

    def _on_selection_changed(self, *_args) -> None:
        self._view_model.table_model.repaint_dirty_rows()
        self._kopiere_markierte_zellen_in_zwischenablage(silent=True)

    def _kopiere_markierte_zellen_in_zwischenablage(self, silent: bool = False) -> None:
        selection_model = self._table.selectionModel()
        if selection_model is None:
            return
        indexes = [index for index in selection_model.selectedIndexes() if index.isValid()]
        if not indexes:
            return

        indexes.sort(key=lambda idx: (idx.row(), idx.column()))
        model = self._view_model.table_model
        zeilen_texte: list[str] = []
        current_row = indexes[0].row()
        current_cells: list[str] = []
        for idx in indexes:
            if idx.row() != current_row:
                zeilen_texte.append("\t".join(current_cells))
                current_cells = []
                current_row = idx.row()
            wert = model.data(idx, Qt.DisplayRole)
            current_cells.append("" if wert is None else str(wert))
        zeilen_texte.append("\t".join(current_cells))

        text = "\n".join(zeilen_texte)
        clipboard = QGuiApplication.clipboard()
        if clipboard is None:
            return
        clipboard.setText(text)

        if not silent:
            self._status_label.setText(
                f"{len(zeilen_texte)} Zeile(n) in die Zwischenablage kopiert."
            )
