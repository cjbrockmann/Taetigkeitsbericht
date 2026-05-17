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
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from External.Presentation.Desktop.krankmeldung_table_model import KrankmeldungRow
from External.Presentation.Desktop.krankmeldung_view_model import KrankmeldungViewModel
from External.Presentation.Desktop.message_boxes import warnung
from External.Presentation.Desktop.form_bearbeitung_dirty import (
    dirty_indices_bei_form_bearbeitung,
    hat_ungespeicherte_formular_aenderungen,
)
from External.Presentation.Desktop.table_view_styles import (
    DirtyRowItemDelegate,
    STANDARD_TABLE_VIEW_STYLESHEET,
)


class KrankmeldungView(QWidget):
    def __init__(
        self, view_model: KrankmeldungViewModel, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._view_model = view_model
        self._initial_load_done = False
        self._suspend_selection_sync = False
        self._bearbeitungs_id: int | None = None
        self._neuanlage_form_snapshot: tuple[str, str, int] = ()
        self._build_ui()
        self._bind_view_model()
        self._reset_formular_defaults()

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

        self._form_group = QGroupBox("Neue Krankmeldung", self)
        self._form_group.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        form_layout = QFormLayout(self._form_group)
        form_layout.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
        )

        locale_de = QLocale(QLocale.Language.German, QLocale.Country.Germany)
        heute_q = QDate(date.today().year, date.today().month, date.today().day)

        self._krank_von_input = QDateEdit(self._form_group)
        self._krank_von_input.setCalendarPopup(True)
        self._krank_von_input.setDisplayFormat("dd.MM.yyyy")
        self._krank_von_input.setLocale(locale_de)
        self._krank_von_input.setDate(heute_q)

        self._krank_bis_input = QDateEdit(self._form_group)
        self._krank_bis_input.setCalendarPopup(True)
        self._krank_bis_input.setDisplayFormat("dd.MM.yyyy")
        self._krank_bis_input.setLocale(locale_de)
        self._krank_bis_input.setDate(heute_q)

        for de in (self._krank_von_input, self._krank_bis_input):
            de.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            de.setFixedWidth(de.sizeHint().width())
        self._krankmeldungstage_spin = QSpinBox(self._form_group)
        self._krankmeldungstage_spin.setRange(0, 366)
        self._krankmeldungstage_spin.setValue(1)
        self._krankmeldungstage_spin.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        self._krankheitstage_hinweis = QLabel("", self._form_group)
        self._krankheitstage_hinweis.setStyleSheet("color: #616161;")
        stage_zeile = QWidget(self._form_group)
        stage_zeile.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        stage_zeile_layout = QHBoxLayout(stage_zeile)
        stage_zeile_layout.setContentsMargins(0, 0, 0, 0)
        stage_zeile_layout.addWidget(self._krankmeldungstage_spin, 0)
        stage_zeile_layout.addWidget(self._krankheitstage_hinweis, 0)
        stage_zeile_layout.addStretch(1)

        form_layout.addRow("Krank von:", self._krank_von_input)
        form_layout.addRow("Krank bis:", self._krank_bis_input)
        form_layout.addRow("Krankheitstage:", stage_zeile)

        self._speichern_button = QPushButton("Krankmeldung speichern", self)
        self._speichern_button.setStyleSheet("QPushButton { color: green; }")
        self._reset_button = QPushButton("Reset", self)
        self._reset_button.setStyleSheet("QPushButton { color: blue; }")
        self._reset_button.setToolTip(
            "Markierung aufheben, Formular zurücksetzen, Krank von/bis auf heute."
        )
        self._loeschen_button = QPushButton("Markierte Zeile löschen", self)
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
        header.resizeSection(2, 72)
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
        self._krank_von_input.dateChanged.connect(self._on_form_changed)
        self._krank_bis_input.dateChanged.connect(self._on_form_changed)
        self._krank_bis_input.dateChanged.connect(
            self._aktualisiere_krankheitstage_eingabehilfe
        )
        self._krankmeldungstage_spin.valueChanged.connect(self._on_form_changed)

    def _on_form_changed(self, *_args) -> None:
        self._update_dirty_rows()

    @staticmethod
    def _kalendertage_inklusiv(von_q: QDate, bis_q: QDate) -> int | None:
        if not von_q.isValid() or not bis_q.isValid():
            return None
        von = date(von_q.year(), von_q.month(), von_q.day())
        bis = date(bis_q.year(), bis_q.month(), bis_q.day())
        if bis < von:
            return None
        return (bis - von).days + 1

    def _aktualisiere_krankheitstage_eingabehilfe(self, *_args) -> None:
        """Hinweis neben Krankheitstage: Kalendertage von–bis (nur Anzeige, kein Auto-Wert)."""
        tage = self._kalendertage_inklusiv(
            self._krank_von_input.date(), self._krank_bis_input.date()
        )
        if tage is None:
            self._krankheitstage_hinweis.setText("")
            return
        if tage == 1:
            self._krankheitstage_hinweis.setText("1 Kalendertag (von–bis)")
        else:
            self._krankheitstage_hinweis.setText(f"{tage} Kalendertage (von–bis)")

    def _on_selection_repaint_dirty(self, *_args) -> None:
        self._view_model.table_model.repaint_dirty_rows()

    def _form_enthaelt_gespeicherte_zeile(self, row: KrankmeldungRow) -> bool:
        try:
            tage_zeile = int(float(row.krankmeldungstage.strip().replace(",", ".")))
        except ValueError:
            tage_zeile = -1
        return (
            row.krank_von == self._krank_von_input.date().toString("dd.MM.yyyy")
            and row.krank_bis == self._krank_bis_input.date().toString("dd.MM.yyyy")
            and tage_zeile == self._krankmeldungstage_spin.value()
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

    def _form_state_snapshot(self) -> tuple[str, str, int]:
        return (
            self._krank_von_input.date().toString("dd.MM.yyyy"),
            self._krank_bis_input.date().toString("dd.MM.yyyy"),
            self._krankmeldungstage_spin.value(),
        )

    def _neuanlage_formular_abweichend(self) -> bool:
        return self._form_state_snapshot() != self._neuanlage_form_snapshot

    @property
    def has_unsaved_changes(self) -> bool:
        model = self._view_model.table_model
        return hat_ungespeicherte_formular_aenderungen(
            dirty_rows=model._dirty_rows,
            bearbeitungs_id=self._bearbeitungs_id,
            neuanlage_formular_abweichend=self._neuanlage_formular_abweichend(),
        )

    def verwerfe_ungespeicherte_aenderungen(self) -> None:
        self._lade_auswahl_jahr()

    def _bind_view_model(self) -> None:
        self._view_model.status_changed.connect(self._status_label.setText)
        self._view_model.error_occurred.connect(self._show_error)

    def _reset_formular_defaults(self) -> None:
        self._bearbeitungs_id = None
        self._view_model.table_model.set_dirty_rows(set())
        heute_q = QDate(date.today().year, date.today().month, date.today().day)
        for de in (self._krank_von_input, self._krank_bis_input):
            de.blockSignals(True)
        self._krank_von_input.setDate(heute_q)
        self._krank_bis_input.setDate(heute_q)
        for de in (self._krank_von_input, self._krank_bis_input):
            de.blockSignals(False)
        self._krankmeldungstage_spin.setValue(1)
        self._aktualisiere_krankheitstage_eingabehilfe()
        self._neuanlage_form_snapshot = self._form_state_snapshot()
        self._aktualisiere_formular_titel()

    def _aktualisiere_formular_titel(self) -> None:
        if self._bearbeitungs_id is not None:
            self._form_group.setTitle("Krankmeldung editieren")
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
            self._form_group.setTitle("Neue Krankmeldung")
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
                "}")

    def _zeile_ins_formular(self, row: KrankmeldungRow) -> None:
        dv = datetime.strptime(row.krank_von, "%d.%m.%Y").date()
        db = datetime.strptime(row.krank_bis, "%d.%m.%Y").date()
        for de in (self._krank_von_input, self._krank_bis_input):
            de.blockSignals(True)
        self._krank_von_input.setDate(QDate(dv.year, dv.month, dv.day))
        self._krank_bis_input.setDate(QDate(db.year, db.month, db.day))
        for de in (self._krank_von_input, self._krank_bis_input):
            de.blockSignals(False)
        self._krankmeldungstage_spin.setValue(
            int(float(row.krankmeldungstage.strip().replace(",", ".")))
        )
        self._aktualisiere_krankheitstage_eingabehilfe()

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
                krank_von_text=self._krank_von_input.date().toString("dd.MM.yyyy"),
                krank_bis_text=self._krank_bis_input.date().toString("dd.MM.yyyy"),
                krankmeldungstage_text=str(self._krankmeldungstage_spin.value()),
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
        warnung(self, "Krankmeldung", message)
