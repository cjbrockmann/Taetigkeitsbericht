from __future__ import annotations

from datetime import date, datetime, timedelta

from pydantic import ValidationError
from PySide6.QtCore import QDate, QLocale, Qt
from PySide6.QtGui import QKeySequence, QShortcut, QShowEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QDoubleSpinBox,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from App.app_config import AppConfig
from External.Presentation.Desktop.message_boxes import frage_ja_nein, warnung
from External.Presentation.Desktop.form_bearbeitung_dirty import (
    dirty_indices_bei_form_bearbeitung,
    hat_ungespeicherte_formular_aenderungen,
)
from External.Presentation.Desktop.table_view_styles import (
    DirtyRowItemDelegate,
    STANDARD_TABLE_VIEW_STYLESHEET,
)
from External.Presentation.Desktop.urlaubsantrag_table_model import UrlaubsantragRow
from External.Presentation.Desktop.urlaubsantrag_view_model import UrlaubsantragViewModel


class UrlaubsantragView(QWidget):
    _STANDARD_URLAUBSTYP = "Jahresurlaub"
    _URLAUBSTYP_AUSWAHL = ("Jahresurlaub", "Sonderurlaub")

    def __init__(
        self,
        view_model: UrlaubsantragViewModel,
        app_config: AppConfig,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._view_model = view_model
        self._initial_load_done = False
        self._bearbeitungs_id: int | None = None
        self._neuanlage_form_snapshot: tuple[str, str, str, str, str] = ()
        self._suspend_selection_sync = False
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

        self._form_group = QGroupBox("Neuer Urlaubsantrag", self)
        self._form_group.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum
        )
        form_layout = QFormLayout(self._form_group)
        form_layout.setSpacing(4)
        form_layout.setContentsMargins(8, 10, 8, 8)

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
        self._datum_von_input.dateChanged.connect(self._on_datum_von_auswahl_geaendert)
        self._datum_bis_input.dateChanged.connect(self._urlaubstage_aus_datum_vorbelegen)

        datum_zeile = QWidget(self._form_group)
        datum_layout = QHBoxLayout(datum_zeile)
        datum_layout.setContentsMargins(0, 0, 0, 0)
        datum_layout.setSpacing(6)
        datum_layout.addWidget(QLabel("von", datum_zeile))
        datum_layout.addWidget(self._datum_von_input)
        datum_layout.addWidget(QLabel("bis", datum_zeile))
        datum_layout.addWidget(self._datum_bis_input)
        datum_layout.addStretch()

        self._urlaubstyp_input = QComboBox(self._form_group)
        self._urlaubstyp_input.setEditable(True)
        self._urlaubstyp_input.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        for urlaubstyp in self._URLAUBSTYP_AUSWAHL:
            self._urlaubstyp_input.addItem(urlaubstyp)
        self._urlaubstyp_input.setCurrentText(self._STANDARD_URLAUBSTYP)
        self._urlaubstyp_input.lineEdit().setPlaceholderText("Jahresurlaub oder Sonderurlaub")
        self._urlaubstage_spin = QDoubleSpinBox(self._form_group)
        self._urlaubstage_spin.setRange(0.0, 366.0)
        self._urlaubstage_spin.setDecimals(1)
        self._urlaubstage_spin.setSingleStep(0.5)
        self._urlaubstage_spin.setLocale(locale_de)
        self._urlaubstage_spin.setValue(1.0)
        self._urlaubstage_spin.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        self._urlaubstage_spin.setFixedWidth(100)
        self._urlaubstage_aus_datum_vorbelegen()

        self._genehmigt_check = QCheckBox("Genehmigt", self._form_group)

        stage_genehmigt_zeile = QWidget(self._form_group)
        stage_genehmigt_layout = QHBoxLayout(stage_genehmigt_zeile)
        stage_genehmigt_layout.setContentsMargins(0, 0, 0, 0)
        stage_genehmigt_layout.setSpacing(12)
        stage_genehmigt_layout.addWidget(self._urlaubstage_spin)
        stage_genehmigt_layout.addWidget(self._genehmigt_check)
        stage_genehmigt_layout.addStretch()

        form_layout.addRow("Zeitraum:", datum_zeile)
        form_layout.addRow("Urlaubstyp:", self._urlaubstyp_input)
        form_layout.addRow("Urlaubstage:", stage_genehmigt_zeile)

        self._speichern_button = QPushButton("Antrag speichern", self)
        self._speichern_button.setSizePolicy(
            QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed
        )

        self._reset_button = QPushButton("Reset", self)
        self._reset_button.setToolTip(
            "Eingabe zuruecksetzen fuer einen neuen Urlaubsantrag."
        )
        self._loeschen_button = QPushButton("Markierten Antrag loeschen", self)
        self._loeschen_button.setToolTip(
            "Loeschen der markierten Tabellenzeile (Taste Entf)."
        )

        _btn_breite_px = 200
        for btn in (
            self._laden_button,
            self._speichern_button,
            self._reset_button,
            self._loeschen_button,
        ):
            btn.setFixedWidth(_btn_breite_px)

        self._speichern_button.setStyleSheet("QPushButton { color: green; }")
        self._reset_button.setStyleSheet("QPushButton { color: blue; }")
        self._loeschen_button.setStyleSheet("QPushButton { color: red; }")

        aktions_spalte = QVBoxLayout()
        aktions_spalte.setSpacing(6)
        aktions_spalte.setContentsMargins(0, 0, 0, 0)
        aktions_spalte.addWidget(self._speichern_button)
        aktions_spalte.addWidget(self._reset_button)
        aktions_spalte.addWidget(self._loeschen_button)

        aktions_wrap = QWidget(self)
        aktions_wrap.setLayout(aktions_spalte)
        aktions_wrap.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum)

        formular_zeile = QHBoxLayout()
        formular_zeile.setContentsMargins(0, 0, 0, 0)
        formular_zeile.addWidget(
            self._form_group,
            stretch=1,
            alignment=Qt.AlignmentFlag.AlignTop,
        )
        formular_zeile.addWidget(
            aktions_wrap,
            stretch=0,
            alignment=Qt.AlignmentFlag.AlignTop,
        )
        formular_zeile.addStretch(1)

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
        header.resizeSection(2, 120)
        header.resizeSection(3, 100)
        header.setStretchLastSection(True)


        self._status_label = QLabel("Bereit.", self)

        root_layout.setSpacing(6)
        root_layout.setContentsMargins(8, 8, 8, 8)

        root_layout.addLayout(toolbar_layout)
        root_layout.addLayout(formular_zeile)
        root_layout.addWidget(self._table)
        root_layout.addWidget(self._status_label)

        loeschen_shortcut = QShortcut(QKeySequence.StandardKey.Delete, self._table)
        loeschen_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        loeschen_shortcut.activated.connect(self._on_loeschen)

        self._laden_button.clicked.connect(self._lade_auswahl_jahr)
        self._jahr_spin.valueChanged.connect(self._on_jahr_changed)
        self._speichern_button.clicked.connect(self._on_speichern)
        self._reset_button.clicked.connect(self._on_neuer_antrag)
        self._loeschen_button.clicked.connect(self._on_loeschen)

        selection_model = self._table.selectionModel()
        if selection_model is not None:
            selection_model.selectionChanged.connect(self._on_tabellen_auswahl_geaendert)
            selection_model.selectionChanged.connect(self._on_selection_repaint_dirty)

    def _on_selection_repaint_dirty(self, *_args) -> None:
        self._view_model.table_model.repaint_dirty_rows()

        self._aktualisiere_formular_titel()
        self._bind_form_dirty_updates()

    def _bind_form_dirty_updates(self) -> None:
        self._datum_von_input.dateChanged.connect(self._on_form_changed)
        self._datum_bis_input.dateChanged.connect(self._on_form_changed)
        self._urlaubstyp_input.currentTextChanged.connect(self._on_form_changed)
        self._urlaubstage_spin.valueChanged.connect(self._on_form_changed)
        self._genehmigt_check.toggled.connect(self._on_form_changed)

    def _on_form_changed(self, *_args) -> None:
        self._update_dirty_rows()

    def _form_enthaelt_gespeicherte_zeile(self, row: UrlaubsantragRow) -> bool:
        genehmigt = "ja" if self._genehmigt_check.isChecked() else "nein"
        try:
            stage_zeile = float(row.urlaubstage.strip().replace(",", "."))
        except ValueError:
            stage_zeile = -1.0
        return (
            row.datum_von == self._datum_von_input.date().toString("dd.MM.yyyy")
            and row.datum_bis == self._datum_bis_input.date().toString("dd.MM.yyyy")
            and row.urlaubstyp.strip() == self._urlaubstyp_input.currentText().strip()
            and row.genehmigt.strip().lower() == genehmigt
            and stage_zeile == self._urlaubstage_spin.value()
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

    def _form_state_snapshot(self) -> tuple[str, str, str, str, str]:
        genehmigt = "ja" if self._genehmigt_check.isChecked() else "nein"
        return (
            self._datum_von_input.date().toString("dd.MM.yyyy"),
            self._datum_bis_input.date().toString("dd.MM.yyyy"),
            self._urlaubstyp_input.currentText().strip(),
            str(self._urlaubstage_spin.value()),
            genehmigt,
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

    def _aktualisiere_formular_titel(self) -> None:
        if self._bearbeitungs_id is not None:
            self._form_group.setTitle("Urlaubsantrag editieren")
            self._form_group.setStyleSheet(
                "QGroupBox {"
                "color: blue;"
                "border: 1px dashed blue;"
                "border-radius: 5px;"
                "margin-top: 14px;"
                "padding-top: 4px;"
                "}"
                "QGroupBox::title {"
                "subcontrol-origin: margin;"
                "subcontrol-position: top left;"
                "left: 12px;"
                "padding: 3px 5px 0px 5px;"
                "}"
            )
        else:
            self._form_group.setTitle("Neuer Urlaubsantrag")
            self._form_group.setStyleSheet("QGroupBox {"
                "border: 1px solid #757575;"
                "border-radius: 5px;"
                "margin-top: 14px;"
                "padding-top: 4px;"
                "}"
                "QGroupBox::title {"
                "subcontrol-origin: margin;"
                "subcontrol-position: top left;"
                "left: 12px;"
                "padding: 3px 5px 0px 5px;"
                "}")
        edit_mode = self._bearbeitungs_id is not None
        self._reset_button.setVisible(edit_mode)
        self._loeschen_button.setVisible(edit_mode)

    @staticmethod
    def _anzahl_werktage_mo_fr(von: date, bis: date) -> int:
        if bis < von:
            return 0
        n = 0
        d = von
        while d <= bis:
            if d.weekday() < 5:
                n += 1
            d += timedelta(days=1)
        return n

    @staticmethod
    def _qdate_nach_date(qd: QDate) -> date:
        return date(qd.year(), qd.month(), qd.day())

    def _on_datum_von_auswahl_geaendert(self, qdatum: QDate) -> None:
        self._datum_bis_input.blockSignals(True)
        self._datum_bis_input.setDate(qdatum)
        self._datum_bis_input.blockSignals(False)
        self._urlaubstage_aus_datum_vorbelegen()

    def _urlaubstage_aus_datum_vorbelegen(self) -> None:
        von = self._qdate_nach_date(self._datum_von_input.date())
        bis = self._qdate_nach_date(self._datum_bis_input.date())
        self._urlaubstage_spin.setValue(float(self._anzahl_werktage_mo_fr(von, bis)))

    def _reset_formular_defaults(self) -> None:
        heute_q = QDate(date.today().year, date.today().month, date.today().day)
        for de in (self._datum_von_input, self._datum_bis_input):
            de.blockSignals(True)
        self._datum_von_input.setDate(heute_q)
        self._datum_bis_input.setDate(heute_q)
        for de in (self._datum_von_input, self._datum_bis_input):
            de.blockSignals(False)
        self._urlaubstage_aus_datum_vorbelegen()
        self._urlaubstyp_input.setCurrentText(self._STANDARD_URLAUBSTYP)
        self._genehmigt_check.setChecked(False)
        self._neuanlage_form_snapshot = self._form_state_snapshot()

    def _zeile_ins_formular(self, row: UrlaubsantragRow) -> None:
        dv = datetime.strptime(row.datum_von, "%d.%m.%Y").date()
        db = datetime.strptime(row.datum_bis, "%d.%m.%Y").date()
        for de in (self._datum_von_input, self._datum_bis_input):
            de.blockSignals(True)
        self._datum_von_input.setDate(QDate(dv.year, dv.month, dv.day))
        self._datum_bis_input.setDate(QDate(db.year, db.month, db.day))
        for de in (self._datum_von_input, self._datum_bis_input):
            de.blockSignals(False)
        self._urlaubstyp_input.setCurrentText(row.urlaubstyp)
        stage_txt = row.urlaubstage.strip().replace(",", ".")
        self._urlaubstage_spin.setValue(float(stage_txt))
        self._genehmigt_check.setChecked(row.genehmigt.strip().lower() == "ja")

    def _on_neuer_antrag(self) -> None:
        self._suspend_selection_sync = True
        try:
            self._table.clearSelection()
        finally:
            self._suspend_selection_sync = False
        self._bearbeitungs_id = None
        self._reset_formular_defaults()
        self._aktualisiere_formular_titel()
        self._view_model.table_model.set_dirty_rows(set())

    def _on_tabellen_auswahl_geaendert(self, *_args) -> None:
        if self._suspend_selection_sync:
            return
        selection_model = self._table.selectionModel()
        if selection_model is None:
            return
        selected_rows = selection_model.selectedRows()
        if not selected_rows:
            return
        row_index = selected_rows[0].row()
        rows = self._view_model.table_model.rows
        if row_index < 0 or row_index >= len(rows):
            return
        row = rows[row_index]
        self._bearbeitungs_id = row.id
        self._zeile_ins_formular(row)
        self._aktualisiere_formular_titel()
        self._update_dirty_rows()

    def _lade_auswahl_jahr(self) -> None:
        self._suspend_selection_sync = True
        try:
            self._view_model.lade_fuer_jahr(self._jahr_spin.value())
        finally:
            self._suspend_selection_sync = False
        self._bearbeitungs_id = None
        self._reset_formular_defaults()
        self._aktualisiere_formular_titel()
        self._view_model.table_model.set_dirty_rows(set())

    def _on_jahr_changed(self, _value: int) -> None:
        self._lade_auswahl_jahr()

    def _on_speichern(self) -> None:
        try:
            self._view_model.speichere_antrag(
                datum_von_text=self._datum_von_input.date().toString("dd.MM.yyyy"),
                datum_bis_text=self._datum_bis_input.date().toString("dd.MM.yyyy"),
                urlaubstyp=self._urlaubstyp_input.currentText(),
                urlaubstage_text=str(self._urlaubstage_spin.value()),
                genehmigt=self._genehmigt_check.isChecked(),
                antrag_id=self._bearbeitungs_id,
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
            self._show_error("Bitte zuerst eine Zeile in der Tabelle markieren.")
            return
        row_index = selected_rows[0].row()
        table_model = self._view_model.table_model
        if row_index < 0 or row_index >= len(table_model.rows):
            self._show_error("Ungueltige Zeilenauswahl.")
            return
        row = table_model.rows[row_index]
        if row.id is None:
            self._show_error(
                "Dieser Eintrag kann nicht geloescht werden (fehlende Datensatz-Id)."
            )
            return
        if not frage_ja_nein(
            self,
            "Urlaubsantrag loeschen",
            f"Urlaubsantrag vom {row.datum_von} bis {row.datum_bis} endgueltig loeschen?",
        ):
            return
        try:
            if self._view_model.loesche_nach_id(row.id):
                self._lade_auswahl_jahr()
        except Exception as exc:  # noqa: BLE001
            self._show_error(str(exc))

    def _show_error(self, message: str) -> None:
        warnung(self, "Urlaubsantrag", message)
