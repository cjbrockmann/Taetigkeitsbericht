from __future__ import annotations

from datetime import time

from PySide6.QtCore import QObject, Signal

from Core.Application.stundenplan_anwendung import StundenplanAnwendung
from Core.Domain.models.models_worktime import Stundenplan
from External.Presentation.Desktop.arbeitszeit_berechnung import zeit_aus_text
from External.Presentation.Desktop.stundenplan_registry import StundenplanRegistry
from External.Presentation.Desktop.stundenplan_table_model import (
    StundenplanRow,
    StundenplanTableModel,
)


class StundenplanViewModel(QObject):
    status_changed = Signal(str)
    error_occurred = Signal(str)

    def __init__(
        self,
        anwendung: StundenplanAnwendung,
        stundenplan_registry: StundenplanRegistry,
    ) -> None:
        super().__init__()
        self._anwendung = anwendung
        self._stundenplan_registry = stundenplan_registry
        self._table_model = StundenplanTableModel()
        self._eintraege_cache: list[Stundenplan] = []
        self._zu_loeschende_ids: list[int] = []

    @property
    def table_model(self) -> StundenplanTableModel:
        return self._table_model

    @property
    def zu_loeschende_ids(self) -> list[int]:
        return list(self._zu_loeschende_ids)

    def lade_alle(self) -> None:
        eintraege = self._anwendung.liste()
        self._eintraege_cache = list(eintraege)
        rows = [self._map_to_row(eintrag) for eintrag in eintraege]
        self._table_model.set_rows(rows)
        self._zu_loeschende_ids.clear()
        self._stundenplan_registry.aktualisiere_aus_zeilen(rows, benachrichtigen=True)
        self.status_changed.emit(
            f"{len(rows)} Stundenplan-Eintrag/-einträge geladen."
        )

    def synchronisiere_registry_mit_tabelle(self) -> None:
        self._stundenplan_registry.aktualisiere_aus_zeilen(
            self._table_model.rows,
            benachrichtigen=True,
        )

    def stundenplan_eintraege_aus_tabelle(self) -> list[Stundenplan]:
        """Alle gueltigen Zeilen der Stundenplan-Tabelle als Domain-Objekte."""
        eintraege: list[Stundenplan] = []
        for row in self._table_model.rows:
            if not (row.uhrzeit_von.strip() and row.uhrzeit_bis.strip()):
                continue
            try:
                eintraege.append(
                    Stundenplan(
                        id=row.id,
                        wochentag=row.wochentag,
                        uhrzeit_von=self._parse_time(row.uhrzeit_von, "uhrzeit_von"),
                        uhrzeit_bis=self._parse_time(row.uhrzeit_bis, "uhrzeit_bis"),
                        pause_beginn=self._parse_optional_time(row.pause_beginn),
                        pause_ende=self._parse_optional_time(row.pause_ende),
                        pause2_beginn=self._parse_optional_time(row.pause2_beginn),
                        pause2_ende=self._parse_optional_time(row.pause2_ende),
                        anmerkung=row.anmerkung or None,
                    )
                )
            except Exception:  # noqa: BLE001
                continue
        if eintraege:
            self._eintraege_cache = list(eintraege)
        return eintraege

    def aktuelle_stundenplan_eintraege(self) -> list[Stundenplan]:
        """In-Memory-Liste fuer Soll-Berechnung: Tabelle (inkl. ungespeichert), sonst letzter Stand."""
        aus_tabelle = self.stundenplan_eintraege_aus_tabelle()
        if aus_tabelle:
            return aus_tabelle
        return list(self._eintraege_cache)

    def add_row(self, position: int | None = None, wochentag: int = 1) -> int:
        return self._table_model.add_empty_row(position=position, wochentag=wochentag)

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
            if isinstance(row.id, int) and row.id not in self._zu_loeschende_ids:
                self._zu_loeschende_ids.append(row.id)
        self._table_model.remove_rows(row_indices)

    def speichere_alle(self) -> bool:
        zeilen_zum_speichern = [
            (zeilen_nummer, row)
            for zeilen_nummer, row in enumerate(self._table_model.rows, start=1)
            if row.uhrzeit_von.strip() or row.uhrzeit_bis.strip()
        ]
        gibt_loeschungen = bool(self._zu_loeschende_ids)

        if not zeilen_zum_speichern and not gibt_loeschungen:
            self.error_occurred.emit(
                "Es gibt keine Änderungen zum Speichern."
            )
            return False

        validierte_eintraege: list[tuple[int, StundenplanRow, Stundenplan]] = []
        validierungs_fehler: list[str] = []
        for zeilen_nummer, row in zeilen_zum_speichern:
            try:
                eintrag = Stundenplan(
                    id=row.id,
                    wochentag=row.wochentag,
                    uhrzeit_von=self._parse_time(row.uhrzeit_von, "uhrzeit_von"),
                    uhrzeit_bis=self._parse_time(row.uhrzeit_bis, "uhrzeit_bis"),
                    pause_beginn=self._parse_optional_time(row.pause_beginn),
                    pause_ende=self._parse_optional_time(row.pause_ende),
                    pause2_beginn=self._parse_optional_time(row.pause2_beginn),
                    pause2_ende=self._parse_optional_time(row.pause2_ende),
                    anmerkung=row.anmerkung or None,
                )
            except Exception as exc:  # noqa: BLE001
                validierungs_fehler.append(f"Zeile {zeilen_nummer}: {exc}")
                continue
            validierte_eintraege.append((zeilen_nummer, row, eintrag))

        if validierungs_fehler:
            self.error_occurred.emit("\n".join(validierungs_fehler))
            return False

        fehler: list[str] = []
        geloescht = 0
        verbleibende_loeschungen: list[int] = []
        for eintrag_id in self._zu_loeschende_ids:
            try:
                if self._anwendung.loesche_per_id(eintrag_id):
                    geloescht += 1
            except Exception as exc:  # noqa: BLE001
                fehler.append(f"Löschen {eintrag_id}: {exc}")
                verbleibende_loeschungen.append(eintrag_id)
        self._zu_loeschende_ids = verbleibende_loeschungen

        erfolgreich = 0
        for zeilen_nummer, row, eintrag in validierte_eintraege:
            try:
                gespeicherter_eintrag = self._anwendung.erfasse(eintrag)
                row.id = gespeicherter_eintrag.id
                erfolgreich += 1
            except Exception as exc:  # noqa: BLE001
                fehler.append(f"Zeile {zeilen_nummer}: {exc}")

        if fehler:
            self.error_occurred.emit("\n".join(fehler))
        self.status_changed.emit(
            f"{erfolgreich} Stundenplan-Eintrag/-einträge gespeichert, "
            f"{geloescht} gelöscht, {len(fehler)} Fehler."
        )
        return not fehler

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
    def _map_to_row(eintrag: Stundenplan) -> StundenplanRow:
        return StundenplanRow(
            id=eintrag.id,
            wochentag=eintrag.wochentag,
            uhrzeit_von=eintrag.uhrzeit_von.strftime("%H:%M"),
            uhrzeit_bis=eintrag.uhrzeit_bis.strftime("%H:%M"),
            pause_beginn=eintrag.pause_beginn.strftime("%H:%M")
            if eintrag.pause_beginn
            else "",
            pause_ende=eintrag.pause_ende.strftime("%H:%M")
            if eintrag.pause_ende
            else "",
            pause2_beginn=eintrag.pause2_beginn.strftime("%H:%M")
            if eintrag.pause2_beginn
            else "",
            pause2_ende=eintrag.pause2_ende.strftime("%H:%M")
            if eintrag.pause2_ende
            else "",
            anmerkung=eintrag.anmerkung or "",
        )
