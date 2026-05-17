from __future__ import annotations

from datetime import date, datetime, time
from typing import Optional
from uuid import UUID

from PySide6.QtCore import QObject, Qt, Signal

from Core.Application.feiertag_anwendung import FeiertagAnwendung
from Core.Application.stundenplan_anwendung import StundenplanAnwendung
from External.Presentation.Desktop.stundenplan_view_model import StundenplanViewModel
from Core.Application.zeiteintrag_anwendung import ZeiteintragAnwendung, ZeiteintragAnwendungDTO
from Core.Domain.models.models_worktime import Stundenplan, Zeiteintrag, ZeiteintragsDTO
from External.Presentation.Desktop.feiertag_registry import FeiertagRegistry
from External.Presentation.Desktop.stundenplan_registry import StundenplanRegistry
from External.Presentation.Desktop.arbeitszeit_berechnung import zeit_aus_text
from External.Presentation.Desktop.zeiteintrag_table_model import ZeiteintragRow, ZeiteintragTableModel


class ZeiteintragViewModel(QObject):
    status_changed = Signal(str)
    error_occurred = Signal(str)
    _selectedYear: int | None = None

    def __init__(
        self,
        anwendung: ZeiteintragAnwendung,
        feiertag_anwendung: FeiertagAnwendung,
        feiertag_registry: FeiertagRegistry,
        stundenplan_anwendung: StundenplanAnwendung,
        stundenplan_registry: StundenplanRegistry,
        stundenplan_view_model: StundenplanViewModel | None = None,
    ) -> None:
        super().__init__()
        self._anwendung = anwendung
        self._feiertag_anwendung = feiertag_anwendung
        self._feiertag_registry = feiertag_registry
        self._stundenplan_anwendung = stundenplan_anwendung
        self._stundenplan_registry = stundenplan_registry
        self._stundenplan_view_model = stundenplan_view_model
        self._table_model = ZeiteintragTableModel()
        self._table_model.set_stundenplan_registry(stundenplan_registry)
        self._suspend_anreicherung = False
        self._zu_loeschende_ids: list[UUID] = []
        self._geladenes_jahr: int | None = None
        self._geladenes_monat: int | None = None
        self._feiertag_registry.feiertage_geaendert.connect(self._auf_feiertage_geaendert)
        self._stundenplan_registry.stundenplan_geaendert.connect(self._auf_stundenplan_geaendert)
        self._table_model.dataChanged.connect(self._on_table_data_changed)


    @property
    def table_model(self) -> ZeiteintragTableModel:
        return self._table_model

    @property
    def zu_loeschende_ids(self) -> list[UUID]:
        return list(self._zu_loeschende_ids)

    def add_row(self, position: int | None = None, datum: str = "") -> int:
        pos = self._table_model.add_empty_row(position=position, datum=datum)
        if datum.strip():
            try:
                self._anreichere_tage({self._parse_date(datum)})
            except ValueError:
                pass
        return pos

    def remove_rows(self, row_indices: list[int]) -> None:
        gueltige_indizes = sorted(
            {
                index
                for index in row_indices
                if 0 <= index < len(self._table_model.rows)
            }
        )
        for index in gueltige_indizes:
            row = self._table_model.rows[index]
            if isinstance(row.id, UUID) and row.id not in self._zu_loeschende_ids:
                self._zu_loeschende_ids.append(row.id)
        self._table_model.remove_rows(row_indices)

    def lade_zeitraum(self, jahr: int, monat: int) -> None:
        feiertage = self._feiertag_anwendung.liste(jahr=jahr)
        self._feiertag_registry.aktualisiere_jahr(jahr, feiertage, benachrichtigen=False)

        stundenplan_eintraege = self._stundenplan_eintraege_fuer_soll()
        if self._stundenplan_view_model is not None:
            self._stundenplan_registry.aktualisiere_aus_zeilen(
                self._stundenplan_view_model.table_model.rows,
                benachrichtigen=False,
            )

        if isinstance(self._anwendung, ZeiteintragAnwendungDTO):
            eintraege = self._anwendung.liste_im_monat(
                jahr=jahr,
                monat=monat,
                stundenplan_eintraege=stundenplan_eintraege,
            )
        else:
            eintraege = self._anwendung.liste_im_monat(jahr=jahr, monat=monat)
        rows = [self._map_to_row(eintrag) for eintrag in eintraege]

        self._table_model.set_rows(rows)
        self._table_model.set_feiertag_nach_datum(
            self._feiertag_registry.snapshot_fuer_monat(jahr, monat)
        )
        self._geladenes_jahr = jahr
        self._geladenes_monat = monat
        self._zu_loeschende_ids.clear()
        self.status_changed.emit(
            f"{len(rows)} Zeile(n) fuer {monat:02d}/{jahr} geladen ({len(eintraege)} aus Datenbank)."
        )

    def _auf_feiertage_geaendert(self, jahr: int) -> None:
        if self._geladenes_jahr is None or self._geladenes_monat is None:
            return
        if jahr != self._geladenes_jahr:
            return
        self._table_model.set_feiertag_nach_datum(
            self._feiertag_registry.snapshot_fuer_monat(
                self._geladenes_jahr,
                self._geladenes_monat,
            )
        )
        self._anreichere_alle_zeilen_in_tabelle()
        self._table_model.feiertag_darstellung_aktualisieren()

    def _on_table_data_changed(self, top_left, bottom_right, roles) -> None:
        if self._suspend_anreicherung:
            return
        if not roles or Qt.ItemDataRole.EditRole not in roles:
            return
        if top_left.column() > 7 or bottom_right.column() < 1:
            return
        daten: set[date] = set()
        for row_index in range(top_left.row(), bottom_right.row() + 1):
            if row_index < 0 or row_index >= len(self._table_model.rows):
                continue
            text = self._table_model.rows[row_index].datum.strip()
            if not text:
                continue
            try:
                daten.add(self._parse_date(text))
            except ValueError:
                continue
        if daten:
            self._anreichere_tage(daten)

    def _anreichere_tage(self, daten: set[date]) -> None:
        if not isinstance(self._anwendung, ZeiteintragAnwendungDTO):
            return
        nach_tag: dict[date, list[tuple[ZeiteintragRow, ZeiteintragsDTO]]] = {}
        for row in self._table_model.rows:
            text = row.datum.strip()
            if not text:
                continue
            try:
                tag = self._parse_date(text)
            except ValueError:
                continue
            if tag not in daten:
                continue
            dto = self._row_to_dto(row)
            nach_tag.setdefault(tag, []).append((row, dto))
        if not nach_tag:
            return
        self._suspend_anreicherung = True
        try:
            for gruppe in nach_tag.values():
                dtos = [dto for _, dto in gruppe]
                self._anwendung.anreichere_eintraege_fuer_tag(dtos)
                for (row, dto) in gruppe:
                    self._apply_dto_to_row(row, dto)
            self._benachrichtige_tabellen_update()
            self._table_model.feiertag_darstellung_aktualisieren()
        finally:
            self._suspend_anreicherung = False

    def _benachrichtige_tabellen_update(self) -> None:
        model = self._table_model
        if not model.rows:
            return
        top = model.index(0, 0)
        bottom = model.index(len(model.rows) - 1, len(model.HEADERS) - 1)
        model.dataChanged.emit(
            top,
            bottom,
            [
                Qt.ItemDataRole.DisplayRole,
                Qt.ItemDataRole.EditRole,
                Qt.ItemDataRole.BackgroundRole,
                Qt.ItemDataRole.ToolTipRole,
                Qt.ItemDataRole.DecorationRole,
            ],
        )

    def _anreichere_alle_zeilen_in_tabelle(self) -> None:
        if not isinstance(self._anwendung, ZeiteintragAnwendungDTO):
            return
        daten: set[date] = set()
        for row in self._table_model.rows:
            text = row.datum.strip()
            if not text:
                continue
            try:
                daten.add(self._parse_date(text))
            except ValueError:
                continue
        if daten:
            self._anreichere_tage(daten)

    def _stundenplan_eintraege_fuer_soll(self) -> list[Stundenplan]:
        """Stundenplan fuer Soll-Berechnung aus der gemeinsamen In-Memory-Liste (kein DB-Zugriff)."""
        if self._stundenplan_view_model is None:
            return []
        return self._stundenplan_view_model.aktuelle_stundenplan_eintraege()

    def _auf_stundenplan_geaendert(self) -> None:
        if self._geladenes_jahr is None or self._geladenes_monat is None:
            return
        self.lade_zeitraum(self._geladenes_jahr, self._geladenes_monat)

    def speichere_alle(self) -> bool:
        zeilen_zum_speichern = [
            (zeilen_nummer, row)
            for zeilen_nummer, row in enumerate(self._table_model.rows, start=1)
            if row.uhrzeit_von.strip() or row.uhrzeit_bis.strip()
        ]
        gibt_loeschungen = bool(self._zu_loeschende_ids)

        if not zeilen_zum_speichern and not gibt_loeschungen:
            self.error_occurred.emit(
                "Es gibt keine Aenderungen zum Speichern."
            )
            return False

        fehler: list[str] = []
        geloescht = 0
        verbleibende_loeschungen: list[UUID] = []
        for eintrag_id in self._zu_loeschende_ids:
            try:
                if self._anwendung.loesche_per_id(eintrag_id):
                    geloescht += 1
            except Exception as exc:  # noqa: BLE001
                fehler.append(f"Loeschen {eintrag_id}: {exc}")
                verbleibende_loeschungen.append(eintrag_id)
        self._zu_loeschende_ids = verbleibende_loeschungen

        erfolgreich = 0
        for zeilen_nummer, row in zeilen_zum_speichern:
            try:
                eintrag = Zeiteintrag(
                    id=row.id,
                    datum=self._parse_date(row.datum),
                    uhrzeit_von=self._parse_time(row.uhrzeit_von, "uhrzeit_von"),
                    uhrzeit_bis=self._parse_time(row.uhrzeit_bis, "uhrzeit_bis"),
                    pause_beginn=self._parse_optional_time(row.pause_beginn),
                    pause_ende=self._parse_optional_time(row.pause_ende),
                    pause2_beginn=self._parse_optional_time(row.pause2_beginn),
                    pause2_ende=self._parse_optional_time(row.pause2_ende),
                    anmerkung=row.anmerkung or None,
                )
                gespeicherter_eintrag = self._anwendung.erfasse(eintrag)
                row.id = gespeicherter_eintrag.id
                erfolgreich += 1
            except Exception as exc:  # noqa: BLE001
                fehler.append(f"Zeile {zeilen_nummer}: {exc}")

        if fehler:
            self.error_occurred.emit("\n".join(fehler))
        self.status_changed.emit(
            f"{erfolgreich} Zeile(n) gespeichert, {geloescht} geloescht, {len(fehler)} Fehler."
        )
        return not fehler

    @staticmethod
    def _parse_date(value: str) -> date:
        return datetime.strptime(value.strip(), "%d.%m.%Y").date()

    @staticmethod
    def _parse_time(value: str, feldname: str) -> time:
        text = value.strip()
        if not text:
            raise ValueError(f"{feldname} darf nicht leer sein.")
        ergebnis = zeit_aus_text(text)
        if ergebnis is None:
            raise ValueError(f"{feldname}: erwartet HH:MM, z. B. 08:30.")
        return ergebnis

    @staticmethod
    def _parse_optional_time(value: str) -> time | None:
        text = value.strip()
        if not text:
            return None
        ergebnis = zeit_aus_text(text)
        if ergebnis is None:
            raise ValueError("Pause: erwartet HH:MM, z. B. 12:00.")
        return ergebnis

    @staticmethod
    def _row_to_dto(row: ZeiteintragRow) -> ZeiteintragsDTO:
        return ZeiteintragsDTO(
            id=row.id,
            datum=ZeiteintragViewModel._parse_date(row.datum),
            uhrzeit_von=ZeiteintragViewModel._parse_optional_time(row.uhrzeit_von),
            uhrzeit_bis=ZeiteintragViewModel._parse_optional_time(row.uhrzeit_bis),
            pause_beginn=ZeiteintragViewModel._parse_optional_time(row.pause_beginn),
            pause_ende=ZeiteintragViewModel._parse_optional_time(row.pause_ende),
            pause2_beginn=ZeiteintragViewModel._parse_optional_time(row.pause2_beginn),
            pause2_ende=ZeiteintragViewModel._parse_optional_time(row.pause2_ende),
            anmerkung=row.anmerkung or None,
        )

    @staticmethod
    def _apply_dto_to_row(row: ZeiteintragRow, eintrag: ZeiteintragsDTO) -> None:
        row.datum = eintrag.datum.strftime("%d.%m.%Y")
        row.uhrzeit_von = (
            eintrag.uhrzeit_von.strftime("%H:%M") if eintrag.uhrzeit_von else ""
        )
        row.uhrzeit_bis = (
            eintrag.uhrzeit_bis.strftime("%H:%M") if eintrag.uhrzeit_bis else ""
        )
        row.pause_beginn = (
            eintrag.pause_beginn.strftime("%H:%M") if eintrag.pause_beginn else ""
        )
        row.pause_ende = (
            eintrag.pause_ende.strftime("%H:%M") if eintrag.pause_ende else ""
        )
        row.pause2_beginn = (
            eintrag.pause2_beginn.strftime("%H:%M") if eintrag.pause2_beginn else ""
        )
        row.pause2_ende = (
            eintrag.pause2_ende.strftime("%H:%M") if eintrag.pause2_ende else ""
        )
        row.anmerkung = eintrag.anmerkung or ""
        row.geleistete_stunden = (
            eintrag.geleistete_stunden.strftime("%H:%M")
            if eintrag.geleistete_stunden
            else ""
        )
        row.soll_stunden_nach_stundenplan = (
            eintrag.soll_stunden_nach_Stundenplan.strftime("%H:%M")
            if eintrag.soll_stunden_nach_Stundenplan
            else ""
        )
        row.soll_stunden_nach_vertrag = (
            eintrag.soll_stunden_nach_vertrag.strftime("%H:%M")
            if eintrag.soll_stunden_nach_vertrag
            else ""
        )
        row.ist_urlaub = eintrag.ist_urlaub
        row.ist_krank = eintrag.ist_krank
        row.ist_feiertag = eintrag.ist_feiertag
        row.ist_ferien = eintrag.ist_ferien
        row.ist_betriebsferien = eintrag.ist_betriebsferien
        row.feiertagsname = eintrag.feiertagsname or ""
        row.schulferienname = eintrag.schulferienname or ""

    @staticmethod
    def _map_to_row(eintrag: ZeiteintragsDTO) -> ZeiteintragRow:
        return ZeiteintragRow(
            id=eintrag.id,
            datum=eintrag.datum.strftime("%d.%m.%Y"),
            uhrzeit_von=eintrag.uhrzeit_von.strftime("%H:%M") if eintrag.uhrzeit_von else "",
            uhrzeit_bis=eintrag.uhrzeit_bis.strftime("%H:%M") if eintrag.uhrzeit_bis else "",
            pause_beginn=eintrag.pause_beginn.strftime("%H:%M")
            if eintrag.pause_beginn
            else "",
            pause_ende=eintrag.pause_ende.strftime("%H:%M") if eintrag.pause_ende else "",
            pause2_beginn=eintrag.pause2_beginn.strftime("%H:%M")
            if eintrag.pause2_beginn
            else "",
            pause2_ende=eintrag.pause2_ende.strftime("%H:%M") if eintrag.pause2_ende else "",
            anmerkung=eintrag.anmerkung or "",
            geleistete_stunden=eintrag.geleistete_stunden.strftime("%H:%M") if eintrag.geleistete_stunden else "",
            soll_stunden_nach_stundenplan=eintrag.soll_stunden_nach_Stundenplan.strftime("%H:%M") if eintrag.soll_stunden_nach_Stundenplan else "",
            soll_stunden_nach_vertrag=eintrag.soll_stunden_nach_vertrag.strftime("%H:%M") if eintrag.soll_stunden_nach_vertrag else "",
            ist_urlaub=eintrag.ist_urlaub,
            ist_krank=eintrag.ist_krank,
            ist_feiertag=eintrag.ist_feiertag,
            ist_ferien=eintrag.ist_ferien,
            ist_betriebsferien=eintrag.ist_betriebsferien,
            feiertagsname=eintrag.feiertagsname or "",
            schulferienname=eintrag.schulferienname or "",
        )
