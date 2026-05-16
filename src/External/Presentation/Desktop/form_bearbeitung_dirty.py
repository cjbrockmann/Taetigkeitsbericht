"""Hilfen: Tabellenzeile rot, wenn Formular-Bearbeitung noch nicht gespeichert ist."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TypeVar

T = TypeVar("T")


def dirty_indices_bei_form_bearbeitung(
    rows: Sequence[T],
    bearbeitungs_id: int | None,
    form_enthaelt_gespeicherte_zeile: Callable[[T], bool],
) -> set[int]:
    """Zeilenindex rot, wenn bearbeitungs_id gesetzt und Formular von der Zeile abweicht."""
    if bearbeitungs_id is None:
        return set()
    dirty: set[int] = set()
    for index, row in enumerate(rows):
        row_id = getattr(row, "id", None)
        if row_id == bearbeitungs_id and not form_enthaelt_gespeicherte_zeile(row):
            dirty.add(index)
    return dirty
