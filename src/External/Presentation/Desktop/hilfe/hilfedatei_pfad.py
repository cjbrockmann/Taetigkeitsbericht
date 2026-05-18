from __future__ import annotations

from pathlib import Path

_HILFE_ORDNER = Path(__file__).resolve().parent


def hilfedatei_zu_pfad(hilfedatei: Path | str) -> Path:
    """Relativer Name → Datei im Hilfe-Ordner; absoluter Pfad bleibt unverändert."""
    p = Path(hilfedatei)
    if p.is_absolute():
        return p
    return (_HILFE_ORDNER / p).resolve()
