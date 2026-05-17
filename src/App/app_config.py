from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final

import tomllib

DEFAULT_ZEITEINTRAG_EXCEL_CELL_SPEC: tuple[int | None, ...] = (
    0,
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    None,
    None,
    11,
    12,
)


def _stunden_zu_hh_mm(wert: Any) -> str:
    if isinstance(wert, bool):
        raise ValueError("stunden darf kein bool sein.")
    if isinstance(wert, int):
        minuten = wert * 60
    elif isinstance(wert, float):
        minuten = int(round(wert * 60))
    elif isinstance(wert, str):
        text = wert.strip()
        if ":" in text:
            teile = text.split(":", 1)
            if len(teile) != 2:
                raise ValueError(f"Ungueltiges Zeitformat: {wert!r}")
            h = int(teile[0])
            m = int(teile[1])
            if h < 0 or not 0 <= m < 60:
                raise ValueError(f"Ungueltige Zeit: {wert!r}")
            minuten = h * 60 + m
        elif text:
            minuten = int(round(float(text) * 60))
        else:
            minuten = 0
    else:
        raise ValueError(f"stunden ungueltig: {wert!r}")
    if minuten < 0:
        raise ValueError("stunden darf nicht negativ sein.")
    h, m = divmod(minuten, 60)
    return f"{h:02d}:{m:02d}"


def _parse_cell_spec(raw: Any) -> tuple[int | None, ...]:
    if raw is None:
        return DEFAULT_ZEITEINTRAG_EXCEL_CELL_SPEC
    if not isinstance(raw, list):
        raise TypeError("zeiteintrag_excel_export.cell_spec muss eine Liste sein.")
    out: list[int | None] = []
    for x in raw:
        if x in ("blank", "empty", "none", None):
            out.append(None)
            continue
        if isinstance(x, bool):
            raise ValueError("cell_spec: boolesche Werte sind nicht erlaubt.")
        if isinstance(x, int):
            if not 0 <= x <= ZEITEINTRAG_SPALTEN_MAX:
                raise ValueError(
                    f"cell_spec: Spaltenindex {x} ungueltig (Zeiteintrag-Tabelle: 0–{ZEITEINTRAG_SPALTEN_MAX})."
                )
            out.append(x)
            continue
        raise ValueError(f"cell_spec: unbekannter Eintrag {x!r} (int oder 'blank').")
    if not out:
        raise ValueError("cell_spec darf nicht leer sein.")
    return tuple(out)


ZEITEINTRAG_SPALTEN_MAX: Final[int] = 12
STUNDENPLAN_SPALTEN_MAX: Final[int] = 8


def _parse_ausgeblendete_spalten(
    raw: Any, max_index: int, pfad_in_config: str
) -> tuple[int, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise TypeError(f"{pfad_in_config} muss eine Liste sein.")
    out: set[int] = set()
    for idx, x in enumerate(raw):
        if isinstance(x, bool):
            raise ValueError(
                f"{pfad_in_config}[{idx}]: boolesche Werte sind nicht erlaubt."
            )
        if not isinstance(x, int):
            raise ValueError(
                f"{pfad_in_config}[{idx}]: erwartet int (Spaltenindex 0–{max_index})."
            )
        if not 0 <= x <= max_index:
            raise ValueError(
                f"{pfad_in_config}[{idx}]: Spalte {x} ungueltig (0–{max_index})."
            )
        out.add(x)
    return tuple(sorted(out))


@dataclass(frozen=True)
class ZeiteintragExcelExportSettings:
    """Einstellungen fuer „Fuer Excel kopieren“ (TSV in Zwischenablage)."""

    include_header: bool = False
    leading_empty_columns: int = 0
    trailing_empty_columns: int = 0
    cell_spec: tuple[int | None, ...] = DEFAULT_ZEITEINTRAG_EXCEL_CELL_SPEC

    def __post_init__(self) -> None:
        if self.leading_empty_columns < 0 or self.trailing_empty_columns < 0:
            raise ValueError("leading/trailing_empty_columns duerfen nicht negativ sein.")


@dataclass(frozen=True)
class AppConfig:
    name: str = "Taetigkeitsbericht"
    version: str = "0.0.0"
    soll_nach_vertrag_nach_wochentag: dict[int, str] = field(default_factory=dict)
    sollstunden_an_feiertagen: bool = False
    kommentar_urlaubstage: str = ""
    kommentar_ueberstunden_frei: str = ""
    zeiteintrag_ausgeblendete_spalten: tuple[int, ...] = ()
    stundenplan_ausgeblendete_spalten: tuple[int, ...] = ()
    zeiteintrag_excel_export: ZeiteintragExcelExportSettings = field(
        default_factory=ZeiteintragExcelExportSettings
    )


def _section_zeiteintrag_excel_export(data: dict[str, Any]) -> ZeiteintragExcelExportSettings:
    sec = data.get("zeiteintrag_excel_export")
    if sec is None:
        return ZeiteintragExcelExportSettings()
    if not isinstance(sec, dict):
        raise TypeError("[zeiteintrag_excel_export] muss eine Tabelle sein.")
    return ZeiteintragExcelExportSettings(
        include_header=bool(sec.get("include_header", False)),
        leading_empty_columns=int(sec.get("leading_empty_columns", 0)),
        trailing_empty_columns=int(sec.get("trailing_empty_columns", 0)),
        cell_spec=_parse_cell_spec(sec.get("cell_spec")),
    )


def _section_zeiteintrag_tabelle(data: dict[str, Any]) -> tuple[int, ...]:
    sec = data.get("zeiteintrag_tabelle")
    if sec is None:
        return ()
    if not isinstance(sec, dict):
        raise TypeError("[zeiteintrag_tabelle] muss eine Tabelle sein.")
    return _parse_ausgeblendete_spalten(
        sec.get("ausgeblendete_spalten"),
        ZEITEINTRAG_SPALTEN_MAX,
        "zeiteintrag_tabelle.ausgeblendete_spalten",
    )


def _section_stundenplan_tabelle(data: dict[str, Any]) -> tuple[int, ...]:
    sec = data.get("stundenplan_tabelle")
    if sec is None:
        return ()
    if not isinstance(sec, dict):
        raise TypeError("[stundenplan_tabelle] muss eine Tabelle sein.")
    return _parse_ausgeblendete_spalten(
        sec.get("ausgeblendete_spalten"),
        STUNDENPLAN_SPALTEN_MAX,
        "stundenplan_tabelle.ausgeblendete_spalten",
    )


def _sollstunden_section(data: dict[str, Any]) -> dict[str, Any]:
    sec = data.get("sollstunden")
    return sec if isinstance(sec, dict) else {}


def _section_sollstunden_an_feiertagen(data: dict[str, Any]) -> bool:
    return bool(_sollstunden_section(data).get("sollstunden_an_feiertagen", False))


def _section_kommentar_urlaubstage(data: dict[str, Any]) -> str:
    wert = _sollstunden_section(data).get("kommentar_urlaubstage", "")
    return str(wert).strip() if wert is not None else ""


def _section_kommentar_ueberstunden_frei(data: dict[str, Any]) -> str:
    wert = _sollstunden_section(data).get("kommentar_ueberstunden_frei", "")
    return str(wert).strip() if wert is not None else ""


def _section_soll_nach_vertrag(data: dict[str, Any]) -> dict[int, str]:
    sec = _sollstunden_section(data)
    if not sec:
        return {}
    wochenstunden = sec.get("wochenstunden")
    if not isinstance(wochenstunden, list):
        return {}
    out: dict[int, str] = {}
    for idx, eintrag in enumerate(wochenstunden, start=1):
        if not isinstance(eintrag, dict):
            raise TypeError(f"sollstunden.wochenstunden[{idx}] muss eine Tabelle sein.")
        if "wochentag" not in eintrag or "stunden" not in eintrag:
            continue
        wt = int(eintrag["wochentag"])
        if not 1 <= wt <= 7:
            raise ValueError(f"wochentag {wt} ungueltig (erwartet 1..7).")
        out[wt] = _stunden_zu_hh_mm(eintrag["stunden"])
    return out


def load_app_config(config_path: Path | None = None) -> AppConfig:
    """Laedt src/config.toml (oder den angegebenen Pfad)."""
    if config_path is None:
        config_path = Path(__file__).resolve().parents[1] / "config.toml"
    if not config_path.is_file():
        return AppConfig()
    with config_path.open("rb") as f:
        data = tomllib.load(f)
    if not isinstance(data, dict):
        return AppConfig()
    return AppConfig(
        name=str(data.get("name", "Taetigkeitsbericht")),
        version=str(data.get("version", "0.0.0")),
        soll_nach_vertrag_nach_wochentag=_section_soll_nach_vertrag(data),
        sollstunden_an_feiertagen=_section_sollstunden_an_feiertagen(data),
        kommentar_urlaubstage=_section_kommentar_urlaubstage(data),
        kommentar_ueberstunden_frei=_section_kommentar_ueberstunden_frei(data),
        zeiteintrag_ausgeblendete_spalten=_section_zeiteintrag_tabelle(data),
        stundenplan_ausgeblendete_spalten=_section_stundenplan_tabelle(data),
        zeiteintrag_excel_export=_section_zeiteintrag_excel_export(data),
    )
