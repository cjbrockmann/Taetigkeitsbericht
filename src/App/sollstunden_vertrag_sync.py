from __future__ import annotations

from pathlib import Path

from App.app_config import (
    SOLLSTUNDEN_VERTRAG_BACKUP_TOML,
    SOLLSTUNDEN_VERTRAG_TOML,
    load_sollstunden_vertraege_from_toml,
)
from Core.Application.sollstunden_vertrag_anwendung import SollstundenVertragAnwendung

SOLLSTUNDEN_VERTRAG_PLATZHALTER = (
    "# Vertragsdaten wurden beim ersten Start in die Datenbank (Tabelle sollstunden_vertrag) importiert.\n"
    "# Die urspruengliche Datei liegt als sollstunden_vertrag_backup.toml vor.\n"
    "# Weitere Aenderungen nur in der Anwendung — diese Datei nicht erneut mit [[sollstunden_vertrag.vertrag]] befuellen.\n"
)


def importiere_sollstunden_vertraege_beim_erststart(
    src_basis: Path,
    anwendung: SollstundenVertragAnwendung,
    *,
    backup_erstellen: bool = False,
) -> bool:
    """
    Importiert Vertraege aus sollstunden_vertrag.toml in die DB.

    Kein Import, wenn die Tabelle sollstunden_vertrag bereits Eintraege hat.

    backup_erstellen (config: sollstunden_vertrag_backup_erstellen): Datei nach
    sollstunden_vertrag_backup.toml verschieben und Platzhalter schreiben; sonst
    sollstunden_vertrag.toml unveraendert lassen.
    """
    if anwendung.hat_eintraege():
        return False

    quelle = src_basis / SOLLSTUNDEN_VERTRAG_TOML
    if not quelle.is_file():
        return False

    vertraege = load_sollstunden_vertraege_from_toml(quelle)
    if not vertraege:
        return False

    for vertrag in vertraege:
        if vertrag.mandant_id is None:
            continue
        anwendung.erfasse(vertrag)

    if backup_erstellen:
        ziel = src_basis / SOLLSTUNDEN_VERTRAG_BACKUP_TOML
        if ziel.is_file():
            ziel.unlink()
        quelle.rename(ziel)
        quelle.write_text(SOLLSTUNDEN_VERTRAG_PLATZHALTER, encoding="utf-8")
    return True
