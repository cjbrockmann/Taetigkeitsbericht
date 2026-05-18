from __future__ import annotations

from datetime import date

from PySide6.QtCore import QDate, QModelIndex, Qt
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QDateEdit,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from External.Presentation.Desktop.feiertag_view_model import FeiertagViewModel
from External.Presentation.Desktop.hilfe import ViewMarkdownHilfe
from External.Presentation.Desktop.message_boxes import warnung
from External.Presentation.Desktop.table_view_styles import (
    FeiertagItemDelegate,
    STANDARD_TABLE_VIEW_STYLESHEET,
)


class FeiertagView(QWidget):
    def __init__(self, view_model: FeiertagViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._view_model = view_model
        self._initial_load_done = False
        self._build_ui()
        self._bind_view_model()

    def showEvent(self, event: QShowEvent) -> None:  # noqa: N802
        super().showEvent(event)
        if self._initial_load_done:
            return
        self._initial_load_done = True
        self._lade_auswahl_jahr()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        toolbar_layout = QHBoxLayout()
        add_layout = QHBoxLayout()

        self._jahr_spin = QSpinBox(self)
        self._jahr_spin.setRange(2000, 2100)
        self._jahr_spin.setValue(date.today().year)
        self._jahr_spin.setPrefix("Jahr: ")
        self._laden_button = QPushButton("Laden", self)
        self._import_button = QPushButton("Aus Internet importieren", self)

        toolbar_layout.addWidget(self._jahr_spin)
        toolbar_layout.addWidget(self._laden_button)
        toolbar_layout.addWidget(self._import_button)

        self._datum_input = QDateEdit(self)
        self._datum_input.setCalendarPopup(True)
        self._datum_input.setDisplayFormat("dd.MM.yyyy")
        self._datum_input.setDate(QDate.currentDate())
        self._bezeichnung_input = QLineEdit(self)
        self._bezeichnung_input.setPlaceholderText("Bezeichnung Feiertag")
        self._halber_tag_check = QCheckBox("Halber Feiertag", self)
        self._offiziell_check = QCheckBox("Offiziell (gesetzlich)", self)
        self._offiziell_check.setChecked(True)
        self._hinzufuegen_button = QPushButton("Feiertag hinzufügen", self)
        self._loeschen_button = QPushButton("Markierten Tag löschen", self)

        add_layout.addWidget(self._datum_input)
        add_layout.addWidget(self._bezeichnung_input)
        add_layout.addWidget(self._halber_tag_check)
        add_layout.addWidget(self._offiziell_check)
        add_layout.addWidget(self._hinzufuegen_button)
        add_layout.addWidget(self._loeschen_button)

        self._table = QTableView(self)
        self._table.setModel(self._view_model.table_model)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setStyleSheet(STANDARD_TABLE_VIEW_STYLESHEET)
        self._table.setItemDelegate(FeiertagItemDelegate(self._table))
        header = self._table.horizontalHeader()
        header.setStretchLastSection(False)
        header.resizeSection(0, 95)
        header.resizeSection(1, 220)
        header.resizeSection(2, 72)
        header.resizeSection(3, 80)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setVisible(True)

        self._status_label = QLabel("Bereit.", self)
        self._markdown_hilfe = ViewMarkdownHilfe(
            self,
            hilfedatei="feiertag.md",
            tooltip="Hilfe zu Feiertagen anzeigen",
            fenster_titel="Hilfe – Feiertage",
        )

        root_layout.addLayout(toolbar_layout)
        root_layout.addLayout(add_layout)
        root_layout.addWidget(self._table)
        fuss_layout = QHBoxLayout()
        fuss_layout.addWidget(self._status_label, 1)
        fuss_layout.addWidget(self._markdown_hilfe.button)
        root_layout.addLayout(fuss_layout)

        self._laden_button.clicked.connect(self._lade_auswahl_jahr)
        self._import_button.clicked.connect(self._on_import_starten)
        self._hinzufuegen_button.clicked.connect(self._on_hinzufuegen)
        self._loeschen_button.clicked.connect(self._on_loeschen)
        self._jahr_spin.valueChanged.connect(self._on_jahr_changed)
        self._view_model.table_model.dataChanged.connect(self._on_table_data_changed)

    def _bind_view_model(self) -> None:
        self._view_model.status_changed.connect(self._status_label.setText)
        self._view_model.error_occurred.connect(self._show_error)

    @property
    def has_unsaved_changes(self) -> bool:
        """Entwurf im Formular „Feiertag hinzufügen“ (nicht Tabellenzeilen — die speichern sofort)."""
        return bool(self._bezeichnung_input.text().strip())

    def _reset_neuanlage_formular(self) -> None:
        self._bezeichnung_input.clear()

    def verwerfe_ungespeicherte_aenderungen(self) -> None:
        self._reset_neuanlage_formular()
        self._lade_auswahl_jahr()

    def _lade_auswahl_jahr(self) -> None:
        self._view_model.lade_fuer_jahr(self._jahr_spin.value())

    def _on_jahr_changed(self, _value: int) -> None:
        self._lade_auswahl_jahr()

    def _on_import_starten(self) -> None:
        try:
            self._view_model.lade_aus_api_und_speichere(jahr=self._jahr_spin.value())
        except Exception as exc:  # noqa: BLE001
            self._show_error(str(exc))

    def _on_hinzufuegen(self) -> None:
        try:
            self._view_model.fuege_feiertag_hinzu(
                datum_text=self._datum_input.date().toString("dd.MM.yyyy"),
                bezeichnung=self._bezeichnung_input.text(),
                ist_halber_tag=self._halber_tag_check.isChecked(),
                ist_offiziell=self._offiziell_check.isChecked(),
            )
            self._reset_neuanlage_formular()
        except Exception as exc:  # noqa: BLE001
            self._show_error(str(exc))

    def _on_table_data_changed(
        self, top_left: QModelIndex, bottom_right: QModelIndex, roles: list[int]
    ) -> None:
        if not roles or Qt.ItemDataRole.EditRole not in roles:
            return
        if top_left.column() not in (2, 3):
            return
        try:
            for row_index in range(top_left.row(), bottom_right.row() + 1):
                self._view_model.speichere_zeile(row_index)
            self._view_model.status_changed.emit("Feiertag aktualisiert.")
        except Exception as exc:  # noqa: BLE001
            self._show_error(str(exc))
            self._lade_auswahl_jahr()

    def _on_loeschen(self) -> None:
        selection_model = self._table.selectionModel()
        if selection_model is None:
            return
        selected_rows = selection_model.selectedRows()
        if not selected_rows:
            self._show_error("Bitte zuerst eine Zeile markieren.")
            return
        row_index = selected_rows[0].row()
        row = self._view_model.table_model.rows[row_index]
        try:
            self._view_model.loesche_nach_datum(row.datum)
            self._lade_auswahl_jahr()
        except Exception as exc:  # noqa: BLE001
            self._show_error(str(exc))

    def _show_error(self, message: str) -> None:
        warnung(self, "Feiertag-Fehler", message)
