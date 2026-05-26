from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime
from uuid import UUID

from PySide6.QtCore import QEvent, QMimeData, QModelIndex, QPersistentModelIndex, QRect, QSize, Qt, QTimer
from PySide6.QtGui import (
    QCloseEvent,
    QColor,
    QGuiApplication,
    QIcon,
    QKeySequence,
    QMouseEvent,
    QPalette,
    QResizeEvent,
    QShortcut,
    QShowEvent,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QStackedLayout,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionHeader,
    QStyleOptionViewItem,
    QTableView,
    QTabWidget,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

from App.app_config import (
    AppConfig,
    Mandant,
    ZeiteintragExcelExportSettings,
    load_zeiteintrag_excel_export_settings,
)
from External.Presentation.Desktop.mandant_auswahl import MandantAuswahl
from External.Presentation.Desktop.betriebsferien_view import BetriebsferienView
from External.Presentation.Desktop.zeiteintrag_excel_clipboard import (
    ExcelExportZelle,
    ExcelZelltyp,
    excel_zelltyp_fuer_spalte,
    setze_excel_zwischenablage,
    zwischenablage_format_hinweis,
    zellenwerte_fuer_excel,
)
from External.Presentation.Desktop.feiertag_view import FeiertagView
from External.Presentation.Desktop.krankmeldung_view import KrankmeldungView
from External.Presentation.Desktop.schulferien_view import SchulferienView
from External.Presentation.Desktop.stundenplan_view import StundenplanView
from External.Presentation.Desktop.mandant_vertical_header import (
    install_mandant_vertical_header,
)
from External.Presentation.Desktop.table_view_styles import (
    DirtyRowItemDelegate,
    ZEITEINTRAG_TABLE_VIEW_STYLESHEET,
    paint_option_mit_zeilenfarbe,
    style_tab_widget,
)
from External.Presentation.Desktop.hilfe import (
    ViewMarkdownHilfe,
    schliesse_gemeinsame_markdown_hilfe,
)
from External.Presentation.Desktop.message_boxes import frage_ja_nein, warnung
from External.Presentation.Desktop.urlaubsantrag_view import UrlaubsantragView
from External.Presentation.Desktop.zeiteintrag_formular import ZeiteintragFormularMonatsFuss
from External.Presentation.Desktop.zeiteintrag_table_model import (
    STATUS_KENNZEICHEN_ICON_MAX_GROESSE,
    STATUS_KENNZEICHEN_ICON_MIN_GROESSE,
    STATUS_KENNZEICHEN_ICON_RAND,
    STATUS_KENNZEICHEN_SPALTE_BREITE,
    ZeiteintragSpalte,
    ZeiteintragTableModel,
)
from External.Presentation.Desktop.zeiteintrag_view_model import ZeiteintragViewModel


class LiveCommitDelegate(DirtyRowItemDelegate):
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
            if index.column() != ZeiteintragSpalte.KOMMENTAR:
                text = text.strip()
            is_live_commit = bool(editor.property("_live_commit"))
            if (
                not is_live_commit
                and index.column() in ZeiteintragSpalte.ZEITFELDER
                and text.isdigit()
            ):
                hour = int(text)
                if 0 <= hour <= 23:
                    text = f"{hour:02d}:00"
            model.setData(index, text)
            return
        super().setModelData(editor, model, index)


class WochentagMitSternDelegate(LiveCommitDelegate):
    """Wochentagskürzel links, Feiertags-Stern-Icon rechts in Spalte 0."""

    def paint(self, painter, option, index):  # noqa: N802
        if index.column() != 0:
            super().paint(painter, option, index)
            return

        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)

        model = index.model()
        is_dirty = (
            model is not None
            and hasattr(model, "is_row_dirty")
            and model.is_row_dirty(index.row())
        )
        opt = paint_option_mit_zeilenfarbe(opt, is_dirty)

        widget = option.widget
        style = widget.style() if widget is not None else None

        painter.save()
        painter.setClipRect(option.rect)

        if style is not None:
            style.drawPrimitive(
                QStyle.PrimitiveElement.PE_PanelItemViewItem,
                opt,
                painter,
                widget,
            )

        text = index.data(Qt.ItemDataRole.DisplayRole)
        text = "" if text is None else str(text)
        icon = index.data(Qt.ItemDataRole.DecorationRole)

        rand = 4
        if isinstance(icon, QIcon) and not icon.isNull():
            icon_breite = 14
            icon_rect = QRect(
                option.rect.right() - rand - icon_breite,
                option.rect.center().y() - icon_breite // 2,
                icon_breite,
                icon_breite,
            )
            text_rect = QRect(
                option.rect.left() + rand,
                option.rect.top(),
                icon_rect.left() - option.rect.left() - rand - 2,
                option.rect.height(),
            )
        else:
            text_rect = option.rect.adjusted(rand, 0, -rand, 0)
            icon_rect = None

        painter.setFont(option.font)
        painter.setPen(opt.palette.color(QPalette.ColorRole.Text))
        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            text,
        )
        if icon_rect is not None:
            icon.paint(painter, icon_rect, Qt.AlignmentFlag.AlignCenter)
        painter.restore()


class StatusKennzeichenDelegate(DirtyRowItemDelegate):
    """Zentriertes Status-Icon in den schmalen Kennzeichen-Spalten."""

    def paint(self, painter, option, index):  # noqa: N802
        if index.column() not in ZeiteintragSpalte.STATUS_KENNZEICHEN:
            super().paint(painter, option, index)
            return

        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)

        model = index.model()
        is_dirty = (
            model is not None
            and hasattr(model, "is_row_dirty")
            and model.is_row_dirty(index.row())
        )
        opt = paint_option_mit_zeilenfarbe(opt, is_dirty)

        widget = option.widget
        style = widget.style() if widget is not None else None

        painter.save()
        painter.setClipRect(option.rect)

        if style is not None:
            style.drawPrimitive(
                QStyle.PrimitiveElement.PE_PanelItemViewItem,
                opt,
                painter,
                widget,
            )

        icon = index.data(Qt.ItemDataRole.DecorationRole)
        if isinstance(icon, QIcon) and not icon.isNull():
            rand = STATUS_KENNZEICHEN_ICON_RAND
            verfuegbar = min(option.rect.width(), option.rect.height())
            groesse = min(
                STATUS_KENNZEICHEN_ICON_MAX_GROESSE,
                max(STATUS_KENNZEICHEN_ICON_MIN_GROESSE, verfuegbar - 2 * rand),
            )
            icon_rect = QRect(
                option.rect.center().x() - groesse // 2,
                option.rect.center().y() - groesse // 2,
                groesse,
                groesse,
            )
            icon.paint(painter, icon_rect, Qt.AlignmentFlag.AlignCenter)

        painter.restore()


class GruppenHeaderView(QHeaderView):
    def __init__(self, orientation: Qt.Orientation, parent=None) -> None:
        super().__init__(orientation, parent)
        self._gruppen = [
            ("Arbeitsphase", ZeiteintragSpalte.VON, ZeiteintragSpalte.BIS),
            ("Pause", ZeiteintragSpalte.PAUSE1_VON, ZeiteintragSpalte.PAUSE1_BIS),
            ("Pause 2", ZeiteintragSpalte.PAUSE2_VON, ZeiteintragSpalte.PAUSE2_BIS),
            (
                "Arbeitsstunden",
                ZeiteintragSpalte.GELEISTET,
                ZeiteintragSpalte.VERTRAG,
            ),
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
        bottom_option.text = str(
            model.headerData(logical_index, Qt.Horizontal, Qt.DisplayRole) or ""
        )
        if logical_index in ZeiteintragSpalte.STATUS_KENNZEICHEN:
            bottom_option.textAlignment = (
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
            )
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
        painter.save()
        painter.setClipRect(gruppen_rect)
        self.style().drawControl(QStyle.ControlElement.CE_Header, top_option, painter, self)
        painter.restore()

    def viewportEvent(self, event):  # noqa: N802
        if event.type() == QEvent.Type.ToolTip:
            logical_index = self.logicalIndexAt(event.pos())
            if logical_index >= 0:
                model = self.model()
                if model is not None:
                    tooltip = model.headerData(
                        logical_index,
                        Qt.Orientation.Horizontal,
                        Qt.ItemDataRole.ToolTipRole,
                    )
                    if tooltip:
                        QToolTip.showText(event.globalPos(), str(tooltip), self)
                        return True
        return super().viewportEvent(event)


class ZeiteintragWindow(QMainWindow):
    _CONTAINER_GRUPPE_BREITE = 300
    _CONTAINER_GRUPPE_HOEHE = 30
    _KOPFZEILE_MANDANT_RAND = 20

    _TAB_ZEITEINTRAEGE = 0
    _TAB_STUNDENPLAN = 1
    _TAB_URLAUB = 2
    _TAB_KRANK = 3
    _TAB_FEIERTAGE = 4
    _TAB_BETRIEBSFERIEN = 5
    _TAB_SCHULFERIEN = 6

    def __init__(
        self,
        view_model: ZeiteintragViewModel,
        stundenplan_view: StundenplanView,
        feiertag_view: FeiertagView,
        urlaubsantrag_view: UrlaubsantragView,
        krankmeldung_view: KrankmeldungView,
        betriebsferien_view: BetriebsferienView,
        schulferien_view: SchulferienView,
        mandant_auswahl: MandantAuswahl,
        app_config: AppConfig,
        excel_export: ZeiteintragExcelExportSettings | None = None,
        ausgeblendete_spalten: Sequence[int] | None = None,
    ) -> None:
        super().__init__()
        self._app_config = app_config
        self._mandant_auswahl = mandant_auswahl
        self._view_model = view_model
        self._stundenplan_view = stundenplan_view
        self._feiertag_view = feiertag_view
        self._urlaubsantrag_view = urlaubsantrag_view
        self._krankmeldung_view = krankmeldung_view
        self._betriebsferien_view = betriebsferien_view
        self._schulferien_view = schulferien_view
        self._excel_export = excel_export or ZeiteintragExcelExportSettings()
        self._ausgeblendete_spalten = tuple(ausgeblendete_spalten or ())
        self._has_unsaved_changes = False
        self._current_loaded_year: int | None = None
        self._current_loaded_month: int | None = None
        self._ignore_period_change = False
        self._suspend_dirty_tracking = False
        self._baseline_rows: list[tuple[object, str, str, str, str, str, str, str, str]] = []
        self._bestaetigter_tab_index = self._TAB_ZEITEINTRAEGE
        self._tab_wechsel_blockiert = False
        self._mandant_wechsel_laeuft = False
        self._mandant_id_vor_popup = mandant_auswahl.mandant_id
        self.setWindowTitle("Tätigkeitsbericht – Erfassung")
        self.resize(1200, 640)
        self._build_ui()
        self._install_mandant_zeilenzaehler()
        self._bind_view_model()
        self._synchronisiere_mandant_views(erstes_laden=True)

    def _erzeuge_container_gruppe(self) -> QFrame:
        """Rahmen ueber allen Tabs mit Mandantenauswahl."""
        rahmen = QFrame(self)
        rahmen.setObjectName("container_gruppe")
        rahmen.setFixedSize(self._CONTAINER_GRUPPE_BREITE, self._CONTAINER_GRUPPE_HOEHE)
        rahmen.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        rahmen.setAutoFillBackground(False)
        rahmen.setStyleSheet(
            "QFrame#container_gruppe {"
            " border: 1px solid black;"
            " border-radius: 6px;"
            " background-color: transparent;"
            " }"
        )

        innen = QHBoxLayout(rahmen)
        innen.setContentsMargins(6, 2, 6, 2)
        innen.setSpacing(6)

        label = QLabel("Mandant:", rahmen)
        label.setStyleSheet("QLabel { background-color: transparent; border: none; }")

        self._mandant_combo_rahmen = QFrame(rahmen)
        self._mandant_combo_rahmen.setObjectName("mandant_combo_rahmen")
        self._mandant_combo_rahmen.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        combo_zeile = QHBoxLayout(self._mandant_combo_rahmen)
        combo_zeile.setContentsMargins(4, 0, 2, 0)
        combo_zeile.setSpacing(0)

        self._mandant_combo = QComboBox(self._mandant_combo_rahmen)
        self._mandant_pfeil_label = QLabel("▼", self._mandant_combo_rahmen)
        self._mandant_pfeil_label.setFixedWidth(16)
        self._mandant_pfeil_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
        )
        self._mandant_pfeil_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self._mandant_pfeil_label.installEventFilter(self)

        for mandant in self._mandant_auswahl.mandanten:
            self._mandant_combo.addItem(mandant.kuerzel, mandant.id)
            self._setze_mandant_combo_eintrag_farben_in_combo(
                self._mandant_combo,
                self._mandant_combo.count() - 1,
                mandant,
            )
        start = self._mandant_combo.findData(self._mandant_auswahl.mandant_id)
        if start >= 0:
            self._mandant_combo.setCurrentIndex(start)
        self._wende_mandant_combo_farben(self._mandant_auswahl.aktueller_mandant())
        self._mandant_combo.installEventFilter(self)
        self._mandant_combo.activated.connect(self._on_mandant_combo_activated)
        self._mandant_auswahl.mandant_id_geaendert.connect(self._sync_mandant_combo)
        self._mandant_auswahl.mandant_id_geaendert.connect(self._on_mandant_id_geaendert)

        combo_zeile.addWidget(self._mandant_combo, 1)
        combo_zeile.addWidget(self._mandant_pfeil_label)

        innen.addWidget(label)
        innen.addWidget(self._mandant_combo_rahmen, 1)
        return rahmen

    def _setze_mandant_combo_eintrag_farben_in_combo(
        self, combo: QComboBox, index: int, mandant: Mandant
    ) -> None:
        model = combo.model()
        model_index = model.index(index, 0)
        model.setData(
            model_index,
            QColor(mandant.foreground_color),
            Qt.ItemDataRole.ForegroundRole,
        )
        model.setData(
            model_index,
            QColor(mandant.background_color),
            Qt.ItemDataRole.BackgroundRole,
        )

    def _wende_mandant_combo_farben(self, mandant: Mandant) -> None:
        fg = QColor(mandant.foreground_color).name(QColor.NameFormat.HexRgb)
        bg = mandant.background_color
        self._mandant_combo_rahmen.setStyleSheet(
            f"QFrame#mandant_combo_rahmen {{"
            f" color: {fg};"
            f" background-color: {bg};"
            " border: 1px solid black;"
            " border-radius: 4px;"
            " }"
        )
        self._mandant_combo.setStyleSheet(
            f"QComboBox {{"
            f" color: {fg};"
            f" background-color: {bg};"
            " border: none;"
            " padding: 1px 2px 1px 4px;"
            " }"
            " QComboBox::drop-down {"
            " width: 0;"
            " border: none;"
            " }"
            " QComboBox::down-arrow {"
            " image: none;"
            " width: 0;"
            " height: 0;"
            " }"
        )
        pfeil_font = self._mandant_pfeil_label.font()
        pfeil_font.setBold(True)
        pfeil_font.setPointSize(11)
        self._mandant_pfeil_label.setFont(pfeil_font)
        self._mandant_pfeil_label.setStyleSheet(
            f"QLabel {{ color: {fg}; background-color: transparent; border: none; }}"
        )

    def _install_mandant_zeilenzaehler(self) -> None:
        mandanten = self._app_config.mandanten
        install_mandant_vertical_header(self._table, mandanten)
        self._stundenplan_view.install_mandant_zeilenzaehler(mandanten)
        self._betriebsferien_view.install_mandant_zeilenzaehler(mandanten)

    def _set_mandant_combo_auf_id(self, mandant_id: int) -> None:
        index = self._mandant_combo.findData(mandant_id)
        if index < 0:
            return
        if self._mandant_combo.currentIndex() == index:
            return
        self._mandant_combo.blockSignals(True)
        try:
            self._mandant_combo.setCurrentIndex(index)
        finally:
            self._mandant_combo.blockSignals(False)

    def _merke_mandant_id_vor_combo_popup(self) -> None:
        self._mandant_id_vor_popup = self._mandant_auswahl.mandant_id

    def _on_mandant_combo_activated(self, index: int) -> None:
        if self._mandant_wechsel_laeuft:
            return
        if index < 0:
            return
        mandant_id = self._mandant_combo.itemData(index)
        if mandant_id is None:
            return
        neuer_mandant_id = int(mandant_id)
        if neuer_mandant_id == self._mandant_id_vor_popup:
            return
        if self._has_unsaved_changes and not self._confirm_discard_mandant_wechsel():
            QTimer.singleShot(
                0,
                lambda: self._mandant_combo_wechsel_zuruecksetzen(self._mandant_id_vor_popup),
            )
            return
        self._fuehre_mandantenwechsel_durch(neuer_mandant_id)

    def _mandant_combo_wechsel_zuruecksetzen(self, mandant_id: int) -> None:
        self._mandant_wechsel_laeuft = True
        try:
            self._set_mandant_combo_auf_id(mandant_id)
            self._wende_mandant_combo_farben(self._mandant_auswahl.aktueller_mandant())
            self._mandant_combo.setFocus(Qt.FocusReason.OtherFocusReason)
        finally:
            self._mandant_wechsel_laeuft = False

    def _fuehre_mandantenwechsel_durch(self, mandant_id: int) -> None:
        self._mandant_wechsel_laeuft = True
        try:
            with self._view_model.anreicherung_ausgesetzt():
                self._mandant_auswahl.set_mandant_id(mandant_id)
        finally:
            self._mandant_wechsel_laeuft = False

    def _sync_mandant_combo(self, mandant_id: int) -> None:
        self._set_mandant_combo_auf_id(mandant_id)
        mandant = self._mandant_auswahl.aktueller_mandant()
        self._wende_mandant_combo_farben(mandant)

    def _on_mandant_id_geaendert(self, _mandant_id: int) -> None:
        self._synchronisiere_mandant_views(erstes_laden=False)

    def _synchronisiere_mandant_views(self, *, erstes_laden: bool) -> None:
        mandant_id = self._mandant_auswahl.mandant_id
        self._view_model.set_mandant_id(mandant_id)
        self._stundenplan_view.set_mandant_id(mandant_id)
        self._betriebsferien_view.set_mandant_id(mandant_id)
        if erstes_laden:
            self._stundenplan_view.bei_mandant_gewechselt()
            self._betriebsferien_view.bei_mandant_gewechselt()
            self._load_selected_period()
        else:
            self._stundenplan_view.bei_mandant_gewechselt()
            self._betriebsferien_view.bei_mandant_gewechselt()
            if (
                self._current_loaded_year is not None
                and self._current_loaded_month is not None
            ):
                self._reload_current_period()

    def _build_ui(self) -> None:
        zeiteintrag_widget = QWidget(self)
        root_layout = QVBoxLayout(zeiteintrag_widget)
        toolbar_layout = QHBoxLayout()

        self._jahr_spin = QSpinBox(self)
        self._jahr_spin.setRange(2000, 2100)
        self._jahr_spin.setValue(date.today().year)
        self._jahr_spin.setPrefix("Jahr: ")
        self._monat_combo = QComboBox(self)
        for monat in range(1, 13):
            self._monat_combo.addItem(f"{monat:02d}", monat)
        self._monat_combo.setCurrentIndex(date.today().month - 1)

        self._laden_button = QPushButton("Zurücksetzen", self)
        self._laden_button.setEnabled(False)
        self._excel_kopieren_button = QPushButton("Für Excel kopieren", self)
        self._excel_kopieren_button.setToolTip(
            "Kopiert alle Zeilen des Monats gemäß cell_spec (config.toml). "
            "Nur Werte werden eingefügt — Rahmen und Format in Excel bleiben erhalten. "
            "Spalten „blank“ (z. B. Geleistet/Soll) werden übersprungen. "
            "In Excel mit Strg+V einfügen."
        )
        self._loesch_hinweis_label = QLabel(self)
        self._loesch_hinweis_label.setStyleSheet("color: red;")
        self._loesch_hinweis_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
        )
        self._loesch_hinweis_label.hide()
        self._zeile_hinzufuegen_button = QPushButton("Zeile hinzufügen", self)
        self._zeile_loeschen_button = QPushButton("Markierte Zeile(n) löschen", self)
        self._speichern_button = QPushButton("Alle Zeilen speichern", self)
        self._status_label = QLabel("Bereit.", self)
        self._status_label.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred
        )
        self._status_label.setWordWrap(True)
        self._status_label_timer = QTimer(self)
        self._status_label_timer.setSingleShot(True)
        self._status_label_timer.setInterval(10_000)
        self._status_label_timer.timeout.connect(self._clear_status_label)
        self._summen_label = QLabel("", self)
        self._summen_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self._markdown_hilfe = ViewMarkdownHilfe(
            zeiteintrag_widget,
            hilfedatei="zeiteintraege.md",
            tooltip="Hilfe zu den Zeiteinträgen anzeigen",
            fenster_titel="Hilfe – Zeiteinträge",
        )
        self._author_label = QLabel("Author: Carlos Brockmann", self)
        self._author_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
        )
        author_mitte = QWidget(self)
        author_mitte_layout = QHBoxLayout(author_mitte)
        author_mitte_layout.setContentsMargins(0, 0, 0, 0)
        author_mitte_layout.addStretch(1)
        author_mitte_layout.addWidget(self._author_label)
        author_mitte_layout.addStretch(1)

        toolbar_layout.addWidget(self._jahr_spin)
        toolbar_layout.addWidget(self._monat_combo)
        toolbar_layout.addWidget(self._excel_kopieren_button)
        toolbar_layout.addStretch(1)
        toolbar_layout.addWidget(self._loesch_hinweis_label)
        toolbar_layout.addStretch(1)
        toolbar_layout.addWidget(self._laden_button)
        toolbar_layout.addWidget(self._zeile_hinzufuegen_button)
        toolbar_layout.addWidget(self._zeile_loeschen_button)
        toolbar_layout.addWidget(self._speichern_button)

        self._table = QTableView(self)
        self._table.setModel(self._view_model.table_model)
        self._table.setHorizontalHeader(GruppenHeaderView(Qt.Horizontal, self._table))
        self._table.setItemDelegate(LiveCommitDelegate(self._table))
        self._table.setItemDelegateForColumn(0, WochentagMitSternDelegate(self._table))
        status_delegate = StatusKennzeichenDelegate(self._table)
        for spalte in ZeiteintragSpalte.STATUS_KENNZEICHEN:
            self._table.setItemDelegateForColumn(spalte, status_delegate)
        self._table.setAlternatingRowColors(True)
        self._table.setShowGrid(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._table.setStyleSheet(ZEITEINTRAG_TABLE_VIEW_STYLESHEET)
        horizontal_header = self._table.horizontalHeader()
        horizontal_header.setStretchLastSection(False)
        horizontal_header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        horizontal_header.resizeSection(ZeiteintragSpalte.TAG, 50)
        horizontal_header.resizeSection(ZeiteintragSpalte.DATUM, 88)
        for spalte in ZeiteintragSpalte.STATUS_KENNZEICHEN:
            horizontal_header.resizeSection(spalte, STATUS_KENNZEICHEN_SPALTE_BREITE)
        for spalte in ZeiteintragSpalte.ZEITFELDER:
            horizontal_header.resizeSection(spalte, ZeiteintragSpalte.ZEIT_SPALTE_BREITE)
        horizontal_header.resizeSection(ZeiteintragSpalte.GELEISTET, 80)
        horizontal_header.resizeSection(ZeiteintragSpalte.SOLL, 72)
        horizontal_header.resizeSection(ZeiteintragSpalte.VERTRAG, 88)
        horizontal_header.resizeSection(
            ZeiteintragSpalte.KOMMENTAR, ZeiteintragSpalte.KOMMENTAR_MIN_BREITE
        )
        horizontal_header.resizeSection(
            ZeiteintragSpalte.INFO, ZeiteintragSpalte.INFO_MIN_BREITE
        )
        horizontal_header.resizeSection(ZeiteintragSpalte.TAG_EXCEL, 34)
        horizontal_header.resizeSection(
            ZeiteintragSpalte.FEIERTAGSNAME, ZeiteintragSpalte.NAME_SPALTE_BREITE
        )
        horizontal_header.resizeSection(
            ZeiteintragSpalte.SCHULFERIENNAME, ZeiteintragSpalte.NAME_SPALTE_BREITE
        )
        self._table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        for spalte in self._ausgeblendete_spalten:
            self._table.setColumnHidden(spalte, True)
        self._aktualisiere_kommentar_breite()
        self._table.verticalHeader().setVisible(True)
        self._table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._table.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self._table.verticalHeader().sectionResized.connect(
            self._aktualisiere_scroll_inhalt_groesse
        )

        self._monats_fuss = ZeiteintragFormularMonatsFuss(zeiteintrag_widget)
        self._ueberstunden_fuss = self._monats_fuss.ueberstunden
        self._urlaub_fuss = self._monats_fuss.urlaub

        self._scroll_inhalt = QWidget(zeiteintrag_widget)
        scroll_inhalt_layout = QVBoxLayout(self._scroll_inhalt)
        scroll_inhalt_layout.setContentsMargins(0, 0, 0, 0)
        scroll_inhalt_layout.setSpacing(0)
        scroll_inhalt_layout.addWidget(self._table)
        scroll_inhalt_layout.addWidget(self._monats_fuss)

        self._table_scroll = QScrollArea(zeiteintrag_widget)
        self._table_scroll.setWidget(self._scroll_inhalt)
        self._table_scroll.setWidgetResizable(True)
        self._table_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._table_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._table_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        root_layout.addLayout(toolbar_layout)
        root_layout.addWidget(self._table_scroll, 1)
        fuss_rechts = QWidget(self)
        fuss_rechts_layout = QHBoxLayout(fuss_rechts)
        fuss_rechts_layout.setContentsMargins(0, 0, 0, 0)
        fuss_rechts_layout.addStretch(1)
        fuss_rechts_layout.addWidget(self._summen_label)
        fuss_rechts_layout.addWidget(self._markdown_hilfe.button)

        fuss_layout = QHBoxLayout()
        fuss_layout.addWidget(self._status_label, 1)
        fuss_layout.addWidget(author_mitte, 1)
        fuss_layout.addWidget(fuss_rechts, 1)
        root_layout.addLayout(fuss_layout)

        self._tab_widget = QTabWidget(self)
        style_tab_widget(self._tab_widget)
        self._tab_widget.addTab(zeiteintrag_widget, "Zeiteinträge")
        self._tab_widget.addTab(self._stundenplan_view, "Stundenplan")
        self._tab_widget.addTab(self._urlaubsantrag_view, "Urlaub")
        self._tab_widget.addTab(self._krankmeldung_view, "Krankmeldung")
        self._tab_widget.addTab(self._feiertag_view, "Feiertage")
        self._tab_widget.addTab(self._betriebsferien_view, "Betriebsferien")
        self._tab_widget.addTab(self._schulferien_view, "Schulferien")

        self._container_gruppe = self._erzeuge_container_gruppe()
        central = QWidget(self)
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(4)

        kopfzeile = QWidget(central)
        kopfzeile.setMinimumHeight(self._CONTAINER_GRUPPE_HOEHE + 8)
        kopfzeile_stack = QStackedLayout(kopfzeile)
        kopfzeile_stack.setStackingMode(QStackedLayout.StackingMode.StackAll)
        kopfzeile_stack.setContentsMargins(10, 4, self._KOPFZEILE_MANDANT_RAND, 0)

        self._app_name_label = QLabel(self._app_config.name, kopfzeile)
        titel_font = self._app_name_label.font()
        titel_font.setBold(True)
        titel_font.setPointSize(titel_font.pointSize() + 2)
        self._app_name_label.setFont(titel_font)
        self._app_name_label.setAlignment(
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
        )
        self._app_name_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        self._app_name_label.setStyleSheet(
            "QLabel { background-color: transparent; border: none; }"
        )
        self._app_name_label.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
        )
        titel_rand = self._CONTAINER_GRUPPE_BREITE + self._KOPFZEILE_MANDANT_RAND
        self._app_name_label.setContentsMargins(titel_rand, 0, titel_rand, 0)

        mandant_zeile = QWidget(kopfzeile)
        mandant_zeile_layout = QHBoxLayout(mandant_zeile)
        mandant_zeile_layout.setContentsMargins(0, 0, 0, 0)
        mandant_zeile_layout.setSpacing(0)
        mandant_zeile_layout.addStretch(1)
        mandant_zeile_layout.addWidget(
            self._container_gruppe,
            alignment=Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
        )
        mandant_zeile_layout.addSpacing(self._KOPFZEILE_MANDANT_RAND)

        kopfzeile_stack.addWidget(self._app_name_label)
        kopfzeile_stack.addWidget(mandant_zeile)
        central_layout.addWidget(kopfzeile)
        central_layout.addWidget(self._tab_widget, 1)
        self.setCentralWidget(central)

        self._tab_widget.tabBar().installEventFilter(self)
        self._tab_widget.currentChanged.connect(self._on_tab_current_changed)

        self._laden_button.clicked.connect(self._on_laden)
        self._excel_kopieren_button.clicked.connect(self._kopiere_tabelle_fuer_excel)
        self._zeile_hinzufuegen_button.clicked.connect(self._on_zeile_hinzufuegen)
        self._zeile_loeschen_button.clicked.connect(self._on_zeile_loeschen)
        self._speichern_button.clicked.connect(self._on_speichern)
        self._table.doubleClicked.connect(self._on_table_double_clicked)
        self._jahr_spin.valueChanged.connect(self._on_period_changed)
        self._monat_combo.currentIndexChanged.connect(self._on_period_changed)

        copy_shortcut = QShortcut(QKeySequence.Copy, self._table)
        copy_shortcut.setContext(Qt.WidgetWithChildrenShortcut)
        copy_shortcut.activated.connect(self._kopiere_markierte_zellen_in_zwischenablage)
        selection_model = self._table.selectionModel()
        if selection_model is not None:
            selection_model.selectionChanged.connect(self._on_selection_changed)

    def _aktualisiere_kommentar_breite(self) -> None:
        """Kommentar: min. KOMMENTAR_MIN_BREITE, Rest Viewport; Info: fest INFO_MIN_BREITE."""
        model = self._table.model()
        if model is None:
            return
        header = self._table.horizontalHeader()
        if not self._table.isColumnHidden(ZeiteintragSpalte.INFO):
            if header.sectionSize(ZeiteintragSpalte.INFO) != ZeiteintragSpalte.INFO_MIN_BREITE:
                header.resizeSection(
                    ZeiteintragSpalte.INFO, ZeiteintragSpalte.INFO_MIN_BREITE
                )
        feste_breite = sum(
            header.sectionSize(col)
            for col in range(model.columnCount())
            if col != ZeiteintragSpalte.KOMMENTAR and not self._table.isColumnHidden(col)
        )
        verfuegbar = max(0, self._table.viewport().width())
        ziel = max(ZeiteintragSpalte.KOMMENTAR_MIN_BREITE, verfuegbar - feste_breite)
        if header.sectionSize(ZeiteintragSpalte.KOMMENTAR) != ziel:
            header.resizeSection(ZeiteintragSpalte.KOMMENTAR, ziel)

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._aktualisiere_kommentar_breite()
        self._aktualisiere_scroll_inhalt_groesse()

    def showEvent(self, event: QShowEvent) -> None:  # noqa: N802
        super().showEvent(event)
        self._aktualisiere_kommentar_breite()
        self._aktualisiere_scroll_inhalt_groesse()

    def _aktualisiere_scroll_inhalt_groesse(self) -> None:
        model = self._table.model()
        if model is None:
            return
        header_h = self._table.horizontalHeader().height()
        zeilen_h = sum(self._table.rowHeight(row) for row in range(model.rowCount()))
        rahmen = self._table.frameWidth() * 2
        tabellen_h = header_h + zeilen_h + rahmen
        self._table.setFixedHeight(max(tabellen_h, 0))

        fuss_widget = self._scroll_inhalt.layout().itemAt(1).widget()
        fuss_h = fuss_widget.sizeHint().height() if fuss_widget is not None else 0
        self._scroll_inhalt.setMinimumHeight(tabellen_h + fuss_h)
        # Breite nicht auf Spaltensumme setzen – sonst horizontaler Scrollbalken
        # an der ScrollArea; die Tabelle nutzt bei Bedarf die eigene horizontale Leiste.

    def _aktualisiere_monats_fuss_monat(self) -> None:
        jahr, monat = self._selected_period()
        self._ueberstunden_fuss.set_monat(jahr, monat)

    def _set_status_text(self, text: str) -> None:
        self._status_label.setText(text)
        self._status_label_timer.stop()
        if text:
            self._status_label_timer.start()

    def _clear_status_label(self) -> None:
        self._status_label.setText("")

    def _bind_view_model(self) -> None:
        self._view_model.status_changed.connect(self._set_status_text)
        self._view_model.error_occurred.connect(self._show_error)
        model = self._view_model.table_model
        model.dataChanged.connect(self._on_model_mutated)
        model.rowsInserted.connect(self._on_model_mutated)
        model.rowsRemoved.connect(self._on_model_mutated)
        model.modelReset.connect(self._on_model_mutated)
        self._view_model.stammdaten_anreicherung_abgeschlossen.connect(
            self._on_stammdaten_anreicherung_abgeschlossen
        )
        self._aktualisiere_summen_anzeige()

    def _on_stammdaten_anreicherung_abgeschlossen(self) -> None:
        """Nach Feiertags-/Stundenplan-Aenderung: Neuberechnung ist kein manueller Entwurf."""
        if self._suspend_dirty_tracking:
            return
        self._capture_baseline()
        self._update_dirty_state()

    def _aktualisiere_summen_anzeige(self) -> None:
        model = self._view_model.table_model
        g_min, s_min = model.summen_geleistet_und_soll_minuten()
        sv_min = model.summe_soll_nach_vertrag_minuten()
        g_txt = ZeiteintragTableModel.minuten_als_hh_mm(g_min)
        s_txt = ZeiteintragTableModel.minuten_als_hh_mm(s_min)
        sv_txt = ZeiteintragTableModel.minuten_als_hh_mm(sv_min)
        self._summen_label.setText(
            f"Geleistet: {g_txt}   |   Soll nach Stundenplan: {s_txt}   |   Soll nach Vertrag: {sv_txt}"
        )
        self._ueberstunden_fuss.set_stunden_summen(g_txt, s_txt, sv_txt)
        monat = self._view_model.monat_mit_guthaben
        if monat is not None:
            self._ueberstunden_fuss.set_guthaben_verrechnung(monat.guthaben.verrechnung)
        self._aktualisiere_monats_fuss_monat()
        self._aktualisiere_scroll_inhalt_groesse()

    def _on_laden(self) -> None:
        if not self._confirm_discard_tab_changes(self._TAB_ZEITEINTRAEGE):
            return
        self._reload_current_period()

    def _on_period_changed(self, *_args) -> None:
        if self._ignore_period_change:
            return
        self._load_selected_period()

    def _selected_period(self) -> tuple[int, int]:
        monat = self._monat_combo.currentData()
        if monat is None:
            monat = date.today().month
        return self._jahr_spin.value(), int(monat)

    def _set_period(self, jahr: int, monat: int) -> None:
        self._ignore_period_change = True
        try:
            self._jahr_spin.setValue(jahr)
            self._monat_combo.setCurrentIndex(monat - 1)
        finally:
            self._ignore_period_change = False

    def _confirm_discard_unsaved_changes(self) -> bool:
        return frage_ja_nein(
            self,
            "Ungespeicherte Änderungen",
            "Es gibt ungespeicherte Zeilen. Beim Wechsel von Jahr/Monat gehen diese verloren. "
            "Trotzdem wechseln?",
        )

    def _confirm_discard_mandant_wechsel(self) -> bool:
        return frage_ja_nein(
            self,
            "Ungespeicherte Änderungen",
            "Es gibt ungespeicherte Zeilen. Beim Mandantenwechsel gehen diese verloren. "
            "Trotzdem wechseln?",
        )

    def _confirm_discard_tab_changes(self, tab_index: int) -> bool:
        if not self._tab_has_unsaved(tab_index):
            return True
        titel = self._tab_widget.tabText(tab_index)
        return frage_ja_nein(
            self,
            "Ungespeicherte Änderungen",
            f"Im Reiter „{titel}“ gibt es ungespeicherte Änderungen. "
            "Verwerfen und fortfahren?",
        )

    def _confirm_close_with_unsaved_changes(self) -> bool:
        return frage_ja_nein(
            self,
            "Ungespeicherte Änderungen",
            "Es gibt ungespeicherte Änderungen. Beim Schließen gehen diese verloren. "
            "Trotzdem schließen?",
        )

    def _tab_has_unsaved(self, tab_index: int) -> bool:
        match tab_index:
            case self._TAB_ZEITEINTRAEGE:
                return self._has_unsaved_changes
            case self._TAB_STUNDENPLAN:
                return self._stundenplan_view.has_unsaved_changes
            case self._TAB_URLAUB:
                return self._urlaubsantrag_view.has_unsaved_changes
            case self._TAB_KRANK:
                return self._krankmeldung_view.has_unsaved_changes
            case self._TAB_FEIERTAGE:
                return self._feiertag_view.has_unsaved_changes
            case self._TAB_BETRIEBSFERIEN:
                return self._betriebsferien_view.has_unsaved_changes
            case self._TAB_SCHULFERIEN:
                return self._schulferien_view.has_unsaved_changes
            case _:
                return False

    def _tab_verwerfe_ungespeichert(self, tab_index: int) -> None:
        match tab_index:
            case self._TAB_ZEITEINTRAEGE:
                self._reload_current_period()
            case self._TAB_STUNDENPLAN:
                self._stundenplan_view.verwerfe_ungespeicherte_aenderungen()
            case self._TAB_URLAUB:
                self._urlaubsantrag_view.verwerfe_ungespeicherte_aenderungen()
            case self._TAB_KRANK:
                self._krankmeldung_view.verwerfe_ungespeicherte_aenderungen()
            case self._TAB_FEIERTAGE:
                self._feiertag_view.verwerfe_ungespeicherte_aenderungen()
            case self._TAB_BETRIEBSFERIEN:
                self._betriebsferien_view.verwerfe_ungespeicherte_aenderungen()
            case self._TAB_SCHULFERIEN:
                self._schulferien_view.verwerfe_ungespeicherte_aenderungen()

    def _on_tab_entered(self, tab_index: int) -> None:
        if tab_index == self._TAB_ZEITEINTRAEGE:
            self._reload_current_period()

    def _finalize_tab_wechsel(self, previous: int, new_index: int) -> None:
        self._tab_verwerfe_ungespeichert(previous)
        self._bestaetigter_tab_index = new_index
        self._on_tab_entered(new_index)

    def _versuche_tab_wechsel_zu(self, target_index: int) -> bool:
        previous = self._bestaetigter_tab_index
        if target_index == previous:
            return True
        if not self._confirm_discard_tab_changes(previous):
            return False
        self._tab_wechsel_blockiert = True
        try:
            self._tab_widget.setCurrentIndex(target_index)
        finally:
            self._tab_wechsel_blockiert = False
        self._finalize_tab_wechsel(previous, target_index)
        return True

    def eventFilter(self, watched, event) -> bool:  # noqa: N802
        if watched is getattr(self, "_mandant_combo", None):
            if event.type() == QEvent.Type.MouseButtonPress:
                mouse = event
                if isinstance(mouse, QMouseEvent) and mouse.button() == Qt.MouseButton.LeftButton:
                    self._merke_mandant_id_vor_combo_popup()
            return super().eventFilter(watched, event)

        if watched is getattr(self, "_mandant_pfeil_label", None):
            if event.type() == QEvent.Type.MouseButtonPress:
                mouse = event
                if isinstance(mouse, QMouseEvent) and mouse.button() == Qt.MouseButton.LeftButton:
                    self._merke_mandant_id_vor_combo_popup()
                    self._mandant_combo.showPopup()
                    return True
            return super().eventFilter(watched, event)

        tab_bar = self._tab_widget.tabBar()
        if watched is tab_bar:
            if event.type() == QEvent.Type.MouseButtonPress:
                mouse = event
                if not isinstance(mouse, QMouseEvent):
                    return super().eventFilter(watched, event)
                if mouse.button() != Qt.MouseButton.LeftButton:
                    return super().eventFilter(watched, event)
                index = tab_bar.tabAt(mouse.position().toPoint())
                if index < 0 or index == self._bestaetigter_tab_index:
                    return super().eventFilter(watched, event)
                if self._versuche_tab_wechsel_zu(index):
                    return True
                return True
            if event.type() == QEvent.Type.KeyPress:
                key = event.key()
                current = self._bestaetigter_tab_index
                count = tab_bar.count()
                if key in (Qt.Key.Key_Left, Qt.Key.Key_Up):
                    target = max(0, current - 1)
                elif key in (Qt.Key.Key_Right, Qt.Key.Key_Down):
                    target = min(count - 1, current + 1)
                elif key == Qt.Key.Key_Home:
                    target = 0
                elif key == Qt.Key.Key_End:
                    target = count - 1
                else:
                    return super().eventFilter(watched, event)
                if target == current:
                    return super().eventFilter(watched, event)
                if self._versuche_tab_wechsel_zu(target):
                    return True
                return True
        return super().eventFilter(watched, event)

    def _on_tab_current_changed(self, new_index: int) -> None:
        if self._tab_wechsel_blockiert:
            return
        previous = self._bestaetigter_tab_index
        if previous == new_index:
            return
        if not self._confirm_discard_tab_changes(previous):
            self._tab_wechsel_blockiert = True
            try:
                self._tab_widget.setCurrentIndex(previous)
            finally:
                self._tab_wechsel_blockiert = False
            return
        self._finalize_tab_wechsel(previous, new_index)

    def _any_tab_has_unsaved(self) -> bool:
        return any(
            self._tab_has_unsaved(tab_index)
            for tab_index in range(self._tab_widget.count())
        )

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        if self._any_tab_has_unsaved() and not self._confirm_close_with_unsaved_changes():
            event.ignore()
            return
        for tab_index in range(self._tab_widget.count()):
            if self._tab_has_unsaved(tab_index):
                self._tab_verwerfe_ungespeichert(tab_index)
        schliesse_gemeinsame_markdown_hilfe()
        event.accept()

    def _load_selected_period(self) -> None:
        selected_year, selected_month = self._selected_period()
        period_changed = (
            self._current_loaded_year != selected_year or self._current_loaded_month != selected_month
        )

        if not period_changed and self._current_loaded_year is not None:
            return

        if self._has_unsaved_changes and period_changed:
            if not self._confirm_discard_unsaved_changes():
                if self._current_loaded_year is not None and self._current_loaded_month is not None:
                    self._set_period(self._current_loaded_year, self._current_loaded_month)
                return

        self._suspend_dirty_tracking = True
        try:
            self._view_model.lade_zeitraum(selected_year, selected_month)
        finally:
            self._suspend_dirty_tracking = False

        self._current_loaded_year = selected_year
        self._current_loaded_month = selected_month
        self._capture_baseline()
        self._has_unsaved_changes = False
        self._view_model.table_model.set_dirty_rows(set())
        self._aktualisiere_zuruecksetzen_button()

    def _on_zeile_hinzufuegen(self) -> None:
        selection_model = self._table.selectionModel()
        position: int | None = None
        datum = ""
        if selection_model is not None:
            selected_rows = [index.row() for index in selection_model.selectedRows()]
            if not selected_rows:
                current_index = selection_model.currentIndex()
                if current_index.isValid():
                    selected_rows = [current_index.row()]
            if selected_rows:
                anchor_row = max(selected_rows)
                position = anchor_row + 1
                model_rows = self._view_model.table_model.rows
                if 0 <= anchor_row < len(model_rows):
                    datum = model_rows[anchor_row].datum

        new_row_index = self._view_model.add_row(position=position, datum=datum)

        if selection_model is not None:
            new_index = self._view_model.table_model.index(new_row_index, 1)
            selection_model.clearSelection()
            self._table.setCurrentIndex(new_index)
            self._table.scrollTo(new_index)

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
        self._capture_baseline()
        self._has_unsaved_changes = False
        self._view_model.table_model.set_dirty_rows(set())
        self._reload_current_period(status_anzeigen=False)
        self._aktualisiere_summen_anzeige()

    def _reload_current_period(self, *, status_anzeigen: bool = True) -> None:
        selected_year, selected_month = self._selected_period()
        self._suspend_dirty_tracking = True
        try:
            self._view_model.lade_zeitraum(
                selected_year, selected_month, status_anzeigen=status_anzeigen
            )
        finally:
            self._suspend_dirty_tracking = False
        self._current_loaded_year = selected_year
        self._current_loaded_month = selected_month
        self._capture_baseline()
        self._has_unsaved_changes = False
        self._view_model.table_model.set_dirty_rows(set())
        self._aktualisiere_zuruecksetzen_button()

    def _on_selection_changed(self, *_args) -> None:
        self._view_model.table_model.repaint_dirty_rows()
        self._kopiere_markierte_zellen_in_zwischenablage(silent=True)

    def _excel_export_typ_sets(self) -> dict[str, frozenset[int]]:
        cfg = self._excel_export
        return {
            "uhrzeit_spalten": frozenset(cfg.uhrzeit_spalten),
            "datum_spalten": frozenset(cfg.datum_spalten),
            "integer_spalten": frozenset(cfg.integer_spalten),
            "float_spalten": frozenset(cfg.float_spalten),
        }

    def _laden_excel_export_config(self) -> bool:
        """cell_spec und Typ-Listen bei jedem Export neu aus config.toml lesen."""
        try:
            self._excel_export = load_zeiteintrag_excel_export_settings()
            return True
        except (OSError, ValueError, TypeError) as exc:
            warnung(
                self,
                "Excel-Export",
                f"[zeiteintrag_excel_export] in config.toml konnte nicht gelesen werden.\n"
                f"Es gilt die letzte gültige Einstellung.\n\n{exc}",
            )
            return False

    def _excel_export_zeile(
        self,
        model: ZeiteintragTableModel,
        zeile: int | None,
        parent: QModelIndex,
    ) -> list[ExcelExportZelle]:
        """zeile=None: Kopfzeile. Ausgabe strikt in cell_spec-Reihenfolge."""
        cfg = self._excel_export
        typ_sets = self._excel_export_typ_sets()
        zellen: list[ExcelExportZelle] = [
            ExcelExportZelle(None, "", "", ExcelZelltyp.TEXT)
            for _ in range(cfg.leading_empty_columns)
        ]
        for spec in cfg.cell_spec:
            if spec is None:
                zellen.append(ExcelExportZelle(None, "", "", ExcelZelltyp.BLANK))
            elif zeile is None:
                kopf = ZeiteintragTableModel.HEADERS[spec]
                zellen.append(ExcelExportZelle(spec, kopf, kopf, ExcelZelltyp.TEXT))
            else:
                wert = model.data(model.index(zeile, spec, parent), Qt.DisplayRole)
                roh = "" if wert is None else str(wert)
                typ = excel_zelltyp_fuer_spalte(spec, **typ_sets)
                tsv, anzeige = zellenwerte_fuer_excel(roh, typ)
                zellen.append(ExcelExportZelle(spec, tsv, anzeige, typ))
        zellen.extend(
            ExcelExportZelle(None, "", "", ExcelZelltyp.TEXT)
            for _ in range(cfg.trailing_empty_columns)
        )
        return zellen

    def _kopiere_tabelle_fuer_excel(self) -> None:
        """Alle Monatszeilen gemaess cell_spec; blank-Spalten ueberspringen, Rest ueberschreiben."""
        if not self._laden_excel_export_config():
            return
        model = self._view_model.table_model
        parent = QModelIndex()
        cfg = self._excel_export
        zeilen: list[list[ExcelExportZelle]] = []
        if cfg.include_header:
            zeilen.append(self._excel_export_zeile(model, None, parent))
        n = model.rowCount(parent)
        for r in range(n):
            zeilen.append(self._excel_export_zeile(model, r, parent))
        clipboard = QGuiApplication.clipboard()
        if clipboard is None:
            return
        ok, formate = setze_excel_zwischenablage(
            zeilen,
            text_spalten=frozenset(cfg.text_spalten),
            spreadsheet_xml_formatierung=cfg.spreadsheet_xml_formatierung,
            kopfzeile=cfg.include_header,
        )
        if not ok:
            warnung(
                self,
                "Excel-Export",
                "Die Zwischenablage konnte nicht vorbereitet werden.",
            )
            return
        spalten = len(zeilen[0]) if zeilen else len(cfg.cell_spec)
        kopf_hinweis = " mit Kopfzeile" if cfg.include_header else ""
        self._set_status_text(
            f"{n} Datenzeile(n){kopf_hinweis}, {spalten} Spalte(n) als "
            f"{zwischenablage_format_hinweis(formate)} kopiert."
        )

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
            zeilen_anzahl = len(zeilen_texte)
            self._set_status_text(
                f"{zeilen_anzahl} Zeile(n) in die Zwischenablage kopiert."
            )

    def _on_table_double_clicked(self, index) -> None:
        if index.column() not in (ZeiteintragSpalte.TAG, ZeiteintragSpalte.DATUM):
            return
        model = self._view_model.table_model
        row_idx = index.row()
        row = model.rows[row_idx]
        datum_text = row.datum.strip()
        if not datum_text:
            datum_text = date.today().strftime("%d.%m.%Y")
            model.setData(model.index(row_idx, ZeiteintragSpalte.DATUM), datum_text)

        try:
            datum = datetime.strptime(datum_text, "%d.%m.%Y").date()
        except ValueError:
            return

        if model.ist_feiertag(datum_text):
            return

        passende_stundenplan_zeilen = self._stundenplan_view.zeilen_fuer_wochentag(
            datum.isoweekday()
        )
        if not passende_stundenplan_zeilen:
            return

        zeiteintrag_zeilen_am_tag = [
            idx
            for idx, zeile in enumerate(model.rows)
            if zeile.datum.strip() == datum_text
        ]
        if row_idx not in zeiteintrag_zeilen_am_tag:
            return

        eintrags_index = zeiteintrag_zeilen_am_tag.index(row_idx)
        if eintrags_index >= len(passende_stundenplan_zeilen):
            return
        stundenplan_zeile = passende_stundenplan_zeilen[eintrags_index]
        self._view_model.uebernehme_stundenplan_in_zeile(row_idx, stundenplan_zeile)

        row = model.rows[row_idx]
        if (
            self._app_config.kommentar_urlaub_krank_modus != "kuerzel"
            and not row.anmerkung.strip()
        ):
            kommentar = stundenplan_zeile.anmerkung.strip()
            if kommentar:
                model.setData(
                    model.index(row_idx, ZeiteintragSpalte.KOMMENTAR), kommentar
                )

    def _show_error(self, message: str) -> None:
        warnung(self, "Fehler beim Speichern/Laden", message)

    def _on_model_mutated(self, *_args) -> None:
        self._aktualisiere_summen_anzeige()
        if self._suspend_dirty_tracking:
            return
        self._update_dirty_state()

    def _capture_baseline(self) -> None:
        self._baseline_rows = self._current_rows_snapshot()

    def _current_rows_snapshot(self) -> list[tuple[object, str, str, str, str, str, str, str, str]]:
        snapshot: list[tuple[object, str, str, str, str, str, str, str, str]] = []
        for row in self._view_model.table_model.rows:
            datum = row.datum.strip()
            uhrzeit_von = row.uhrzeit_von.strip()
            uhrzeit_bis = row.uhrzeit_bis.strip()
            pause_beginn = row.pause_beginn.strip()
            pause_ende = row.pause_ende.strip()
            pause2_beginn = row.pause2_beginn.strip()
            pause2_ende = row.pause2_ende.strip()
            anmerkung = row.anmerkung.strip()
            if not self._is_row_relevant_for_unsaved(uhrzeit_von, uhrzeit_bis):
                continue
            snapshot.append(
                (
                    row.id,
                    datum,
                    uhrzeit_von,
                    uhrzeit_bis,
                    pause_beginn,
                    pause_ende,
                    pause2_beginn,
                    pause2_ende,
                    anmerkung,
                )
            )
        return snapshot

    def _aktualisiere_zuruecksetzen_button(self) -> None:
        aktiv = self._has_unsaved_changes
        self._laden_button.setEnabled(aktiv)
        if aktiv:
            self._laden_button.setStyleSheet("QPushButton { color: red; }")
        else:
            self._laden_button.setStyleSheet("")
        anzahl = len(self._view_model.zu_loeschende_ids)
        if anzahl == 0:
            self._loesch_hinweis_label.hide()
        else:
            wort = "Zeile" if anzahl == 1 else "Zeilen"
            self._loesch_hinweis_label.setText(f"{anzahl} {wort} zu löschen")
            self._loesch_hinweis_label.show()

    def _update_dirty_state(self) -> None:
        self._has_unsaved_changes = (
            self._current_rows_snapshot() != self._baseline_rows
            or bool(self._view_model.zu_loeschende_ids)
        )
        self._view_model.table_model.set_dirty_rows(self._compute_dirty_row_indices())
        self._aktualisiere_zuruecksetzen_button()

    def _compute_dirty_row_indices(self) -> set[int]:
        baseline_by_id: dict[UUID, tuple[str, str, str, str, str, str, str, str]] = {
            row_id: (
                datum,
                uhrzeit_von,
                uhrzeit_bis,
                pause_beginn,
                pause_ende,
                pause2_beginn,
                pause2_ende,
                anmerkung,
            )
            for (
                row_id,
                datum,
                uhrzeit_von,
                uhrzeit_bis,
                pause_beginn,
                pause_ende,
                pause2_beginn,
                pause2_ende,
                anmerkung,
            ) in self._baseline_rows
            if isinstance(row_id, UUID)
        }
        dirty_rows: set[int] = set()
        for index, row in enumerate(self._view_model.table_model.rows):
            datum = row.datum.strip()
            uhrzeit_von = row.uhrzeit_von.strip()
            uhrzeit_bis = row.uhrzeit_bis.strip()
            pause_beginn = row.pause_beginn.strip()
            pause_ende = row.pause_ende.strip()
            pause2_beginn = row.pause2_beginn.strip()
            pause2_ende = row.pause2_ende.strip()
            anmerkung = row.anmerkung.strip()

            if not self._is_row_relevant_for_unsaved(uhrzeit_von, uhrzeit_bis):
                continue

            if row.id is None:
                dirty_rows.add(index)
                continue

            baseline_values = baseline_by_id.get(row.id)
            current_values = (
                datum,
                uhrzeit_von,
                uhrzeit_bis,
                pause_beginn,
                pause_ende,
                pause2_beginn,
                pause2_ende,
                anmerkung,
            )
            if baseline_values != current_values:
                dirty_rows.add(index)

        return dirty_rows

    @staticmethod
    def _is_row_relevant_for_unsaved(uhrzeit_von: str, uhrzeit_bis: str) -> bool:
        return bool(uhrzeit_von)
