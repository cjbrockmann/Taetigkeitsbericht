from __future__ import annotations

from datetime import date, datetime

from pydantic import ValidationError
from PySide6.QtCore import QDate, QLocale, Qt
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDateEdit,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from External.Presentation.Desktop.betriebsferien_table_model import BetriebsferienRow
from External.Presentation.Desktop.betriebsferien_view_model import BetriebsferienViewModel
from External.Presentation.Desktop.form_bearbeitung_dirty import dirty_indices_bei_form_bearbeitung
from External.Presentation.Desktop.table_view_styles import (
    DirtyRowItemDelegate,
    STANDARD_TABLE_VIEW_STYLESHEET,
)


class BetriebsferienView(QWidget):
    def __init__(
        self, view_model: BetriebsferienViewModel, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._view_model = view_model
        self._initial_load_done = False
        self._suspend_selection_sync = False
        self._bearbeitungs_id: int | None = None
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

        self._jahr_spin = QSpinBox(self)
        self._jahr_spin.setRange(2000, 2100)
        self._jahr_spin.setValue(date.today().year)
        self._jahr_spin.setPrefix("Jahr: ")
        self._laden_button = QPushButton("Laden", self)

        toolbar_layout.addWidget(self._jahr_spin)
        toolbar_layout.addWidget(self._laden_button)
        toolbar_layout.addStretch()

        self._form_group = QGroupBox("Neue Betriebsferien", self)
        self._form_group.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        form_layout = QFormLayout(self._form_group)
        form_layout.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
        )

        locale_de = QLocale(QLocale.Language.German, QLocale.Country.Germany)
        heute_q = QDate(date.today().year, date.today().month, date.today().day)

        self._datum_von_input = QDateEdit(self._form_group)
        self._datum_von_input.setCalendarPopup(True)
        self._datum_von_input.setDisplayFormat("dd.MM.yyyy")
        self._datum_von_input.setLocale(locale_de)
        self._datum_von_input.setDate(heute_q)

        self._datum_bis_input = QDateEdit(self._form_group)
        self._datum_bis_input.setCalendarPopup(True)
        self._datum_bis_input.setDisplayFormat("dd.MM.yyyy")
        self._datum_bis_input.setLocale(locale_de)
        self._datum_bis_input.setDate(heute_q)

        for de in (self._datum_von_input, self._datum_bis_input):
            de.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            de.setFixedWidth(de.sizeHint().width())

        self._name_input = QLineEdit(self._form_group)
        self._name_input.setPlaceholderText("z. B. Betriebsschliessung")
        self._anmerkung_input = QLineEdit(self._form_group)
        self._anmerkung_input.setPlaceholderText("optional")

        form_layout.addRow("Von:", self._datum_von_input)
        form_layout.addRow("Bis:", self._datum_bis_input)
        form_layout.addRow("Bezeichnung:", self._name_input)
        form_layout.addRow("Anmerkung:", self._anmerkung_input)

        self._speichern_button = QPushButton("Betriebsferien speichern", self)
        self._speichern_button.setStyleSheet("QPushButton { color: green; }")
        self._reset_button = QPushButton("Reset", self)
        self._reset_button.setStyleSheet("QPushButton { color: blue; }")
        self._reset_button.setToolTip(
            "Markierung aufheben, Formular zuruecksetzen, Von/Bis auf heute."
        )
        self._loeschen_button = QPushButton("Markierte Zeile loeschen", self)
        self._loeschen_button.setStyleSheet("QPushButton { color: red; }")

        _btn_breite = 220
        for btn in (self._speichern_button, self._reset_button, self._loeschen_button):
            btn.setFixedWidth(_btn_breite)

        form_linke_seite = QWidget(self)
        form_linke_layout = QVBoxLayout(form_linke_seite)
        form_linke_layout.setContentsMargins(0, 0, 0, 0)
        form_linke_layout.addWidget(self._form_group)

        aktions_wrap = QWidget(self)
        aktions_spalte = QVBoxLayout(aktions_wrap)
        aktions_spalte.setSpacing(6)
        aktions_spalte.setContentsMargins(0, 20, 0, 0)
        _btn_links = Qt.AlignmentFlag.AlignLeft
        aktions_spalte.addWidget(self._speichern_button, 0, _btn_links)
        aktions_spalte.addWidget(self._reset_button, 0, _btn_links)
        aktions_spalte.addWidget(self._loeschen_button, 0, _btn_links)
        aktions_spalte.addStretch(1)
        aktions_wrap.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum
        )

        oberer_zeile = QHBoxLayout()
        oberer_zeile.setContentsMargins(0, 0, 0, 0)
        _oben = Qt.AlignmentFlag.AlignTop
        oberer_zeile.addWidget(form_linke_seite, stretch=1, alignment=_oben)
        oberer_zeile.addWidget(aktions_wrap, stretch=1, alignment=_oben)

        self._table = QTableView(self)
        self._table.setModel(self._view_model.table_model)
        self._table.setItemDelegate(DirtyRowItemDelegate(self._table))
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setStyleSheet(STANDARD_TABLE_VIEW_STYLESHEET)
        header = self._table.horizontalHeader()
        header.resizeSection(0, 95)
        header.resizeSection(1, 95)
        header.resizeSection(2, 160)
        header.setStretchLastSection(True)

        self._status_label = QLabel("Bereit.", self)

        root_layout.addLayout(toolbar_layout)
        root_layout.addLayout(oberer_zeile)
        root_layout.addWidget(self._table, stretch=1)
        root_layout.addWidget(self._status_label)

        self._laden_button.clicked.connect(self._lade_auswahl_jahr)
        self._jahr_spin.valueChanged.connect(self._on_jahr_changed)
        self._speichern_button.clicked.connect(self._on_speichern)
        self._reset_button.clicked.connect(self._on_reset)
        self._loeschen_button.clicked.connect(self._on_loeschen)

        selection_model = self._table.selectionModel()
        if selection_model is not None:
            selection_model.selectionChanged.connect(self._on_tabellen_auswahl_geaendert)
            selection_model.selectionChanged.connect(self._on_selection_repaint_dirty)

        self._aktualisiere_selektions_buttons()
        self._bind_form_dirty_updates()

    def _bind_form_dirty_updates(self) -> None:
        self._datum_von_input.dateChanged.connect(self._on_form_changed)
        self._datum_bis_input.dateChanged.connect(self._on_form_changed)
        self._name_input.textChanged.connect(self._on_form_changed)
        self._anmerkung_input.textChanged.connect(self._on_form_changed)

    def _on_form_changed(self, *_args) -> None:
        self._update_dirty_rows()

    def _on_selection_repaint_dirty(self, *_args) -> None:
        self._view_model.table_model.repaint_dirty_rows()

    def _form_enthaelt_gespeicherte_zeile(self, row: BetriebsferienRow) -> bool:
        return (
            row.datum_von == self._datum_von_input.date().toString("dd.MM.yyyy")
            and row.datum_bis == self._datum_bis_input.date().toString("dd.MM.yyyy")
            and row.name.strip() == self._name_input.text().strip()
            and row.anmerkung.strip() == self._anmerkung_input.text().strip()
        )

    def _update_dirty_rows(self) -> None:
        model = self._view_model.table_model
        model.set_dirty_rows(
            dirty_indices_bei_form_bearbeitung(
                model.rows,
                self._bearbeitungs_id,
                self._form_enthaelt_gespeicherte_zeile,
            )
        )

    def _bind_view_model(self) -> None:
        self._view_model.status_changed.connect(self._status_label.setText)
        self._view_model.error_occurred.connect(self._show_error)

    def _reset_formular_defaults(self) -> None:
        self._bearbeitungs_id = None
        self._view_model.table_model.set_dirty_rows(set())
        heute_q = QDate(date.today().year, date.today().month, date.today().day)
        for de in (self._datum_von_input, self._datum_bis_input):
            de.blockSignals(True)
        self._datum_von_input.setDate(heute_q)
        self._datum_bis_input.setDate(heute_q)
        for de in (self._datum_von_input, self._datum_bis_input):
            de.blockSignals(False)
        self._name_input.clear()
        self._anmerkung_input.clear()
        self._aktualisiere_formular_titel()

    def _aktualisiere_formular_titel(self) -> None:
        if self._bearbeitungs_id is not None:
            self._form_group.setTitle("Betriebsferien editieren")
            self._form_group.setStyleSheet(
                "QGroupBox {"
                "border: 1px dashed blue;"
                "border-radius: 5px;"
                "margin-top: 14px;"
                "padding-top: 4px;"
                "}"
                "QGroupBox::title { "
                "subcontrol-origin: margin; color: blue; "
                "left: 12px;"
                "padding: 3px 5px 0px 5px;"
                "}"
            )
        else:
            self._form_group.setTitle("Neue Betriebsferien")
            self._form_group.setStyleSheet(
                "QGroupBox {"
                "border: 1px solid #757575;"
                "border-radius: 5px;"
                "margin-top: 14px;"
                "padding-top: 4px;"
                "}"
                "QGroupBox::title { "
                "subcontrol-origin: margin; color: black; "
                "left: 12px;"
                "padding: 3px 5px 0px 5px;"
                "}"
            )

    def _zeile_ins_formular(self, row: BetriebsferienRow) -> None:
        dv = datetime.strptime(row.datum_von, "%d.%m.%Y").date()
        db = datetime.strptime(row.datum_bis, "%d.%m.%Y").date()
        for de in (self._datum_von_input, self._datum_bis_input):
            de.blockSignals(True)
        self._datum_von_input.setDate(QDate(dv.year, dv.month, dv.day))
        self._datum_bis_input.setDate(QDate(db.year, db.month, db.day))
        for de in (self._datum_von_input, self._datum_bis_input):
            de.blockSignals(False)
        self._name_input.setText(row.name)
        self._anmerkung_input.setText(row.anmerkung)

    def _aktualisiere_selektions_buttons(self) -> None:
        sm = self._table.selectionModel()
        hat_zeile = False
        if sm is not None:
            hat_zeile = bool(sm.selectedRows())
        self._reset_button.setVisible(hat_zeile)
        self._loeschen_button.setVisible(hat_zeile)

    def _on_tabellen_auswahl_geaendert(self, *_args) -> None:
        if self._suspend_selection_sync:
            return
        sm = self._table.selectionModel()
        if sm is None:
            return
        selected = sm.selectedRows()
        if not selected:
            self._reset_formular_defaults()
            self._aktualisiere_selektions_buttons()
            return
        row_index = selected[0].row()
        rows = self._view_model.table_model.rows
        if row_index < 0 or row_index >= len(rows):
            return
        row = rows[row_index]
        self._bearbeitungs_id = row.id
        self._zeile_ins_formular(row)
        self._aktualisiere_formular_titel()
        self._aktualisiere_selektions_buttons()
        self._update_dirty_rows()

    def _on_reset(self) -> None:
        self._table.clearSelection()
        self._view_model.table_model.set_dirty_rows(set())

    def _lade_auswahl_jahr(self) -> None:
        self._suspend_selection_sync = True
        try:
            self._table.clearSelection()
        finally:
            self._suspend_selection_sync = False
        self._view_model.lade_fuer_jahr(self._jahr_spin.value())
        self._reset_formular_defaults()
        self._aktualisiere_selektions_buttons()
        self._view_model.table_model.set_dirty_rows(set())

    def _on_jahr_changed(self, _value: int) -> None:
        self._lade_auswahl_jahr()

    def _on_speichern(self) -> None:
        try:
            self._view_model.speichere_eintrag(
                datum_von_text=self._datum_von_input.date().toString("dd.MM.yyyy"),
                datum_bis_text=self._datum_bis_input.date().toString("dd.MM.yyyy"),
                name=self._name_input.text(),
                anmerkung_text=self._anmerkung_input.text(),
                eintrag_id=self._bearbeitungs_id,
            )
            self._lade_auswahl_jahr()
        except (ValueError, ValidationError) as exc:
            self._show_error(str(exc))

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
            self._view_model.loesche_nach_id(row.id)
            self._lade_auswahl_jahr()
        except Exception as exc:  # noqa: BLE001
            self._show_error(str(exc))

    def _show_error(self, message: str) -> None:
        QMessageBox.warning(self, "Betriebsferien", message)
