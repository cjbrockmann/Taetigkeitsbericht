from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final

import tomllib

DEFAULT_ZEITEINTRAG_EXCEL_UHRZEIT_SPALTEN: tuple[int, ...] = (7, 8, 9, 10, 11, 12)
DEFAULT_ZEITEINTRAG_EXCEL_DATUM_SPALTEN: tuple[int, ...] = (1,)
DEFAULT_ZEITEINTRAG_EXCEL_INTEGER_SPALTEN: tuple[int, ...] = ()
DEFAULT_ZEITEINTRAG_EXCEL_FLOAT_SPALTEN: tuple[int, ...] = ()
DEFAULT_ZEITEINTRAG_EXCEL_TEXT_SPALTEN: tuple[int, ...] = (17,)

DEFAULT_ZEITEINTRAG_EXCEL_CELL_SPEC: tuple[int | None, ...] = (
    0,
    17,
    7,
    8,
    9,
    10,
    11,
    12,
    None,
    None,
    16,
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


ZEITEINTRAG_SPALTEN_MAX: Final[int] = 20

KOMMENTAR_URLAUB_KRANK_MODI: Final[frozenset[str]] = frozenset({"praefix", "kuerzel"})
DEFAULT_KOMMENTAR_URLAUB_KRANK_MODUS: Final[str] = "praefix"
STUNDENPLAN_SPALTEN_MAX: Final[int] = 8
DEFAULT_ZEITEINTRAG_GRAUER_HINTERGRUND_SPALTEN: Final[tuple[int, ...]] = (2, 3, 4, 5, 6)


def _parse_spalten_indizes(
    raw: Any,
    max_index: int,
    pfad_in_config: str,
    *,
    default: tuple[int, ...] | None = None,
) -> tuple[int, ...]:
    if raw is None:
        return default if default is not None else ()
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


def _parse_ausgeblendete_spalten(
    raw: Any, max_index: int, pfad_in_config: str
) -> tuple[int, ...]:
    return _parse_spalten_indizes(raw, max_index, pfad_in_config)


@dataclass(frozen=True)
class Mandant:
    name: str
    id: int
    foreground_color: str = "#000000"
    background_color: str = "#FFFFFF"
    rowcounter_color: str = "#000000"


@dataclass(frozen=True)
class MandantWochenstunden:
    """Vertrags-Soll je Wochentag und Summe — pro Mandant ([[wochenstunden.mandant]])."""

    mandant_id: int
    soll_nach_vertrag_nach_wochentag: dict[int, str] = field(default_factory=dict)
    wochenstunden_summe: float = 0.0


@dataclass(frozen=True)
class ZeiteintragExcelExportSettings:
    """Einstellungen fuer „Fuer Excel kopieren“ (TSV + HTML in Zwischenablage)."""

    include_header: bool = False
    leading_empty_columns: int = 0
    trailing_empty_columns: int = 0
    cell_spec: tuple[int | None, ...] = DEFAULT_ZEITEINTRAG_EXCEL_CELL_SPEC
    uhrzeit_spalten: tuple[int, ...] = DEFAULT_ZEITEINTRAG_EXCEL_UHRZEIT_SPALTEN
    datum_spalten: tuple[int, ...] = DEFAULT_ZEITEINTRAG_EXCEL_DATUM_SPALTEN
    integer_spalten: tuple[int, ...] = DEFAULT_ZEITEINTRAG_EXCEL_INTEGER_SPALTEN
    float_spalten: tuple[int, ...] = DEFAULT_ZEITEINTRAG_EXCEL_FLOAT_SPALTEN
    text_spalten: tuple[int, ...] = DEFAULT_ZEITEINTRAG_EXCEL_TEXT_SPALTEN
    html_formatierung: bool = True

    def __post_init__(self) -> None:
        if self.leading_empty_columns < 0 or self.trailing_empty_columns < 0:
            raise ValueError("leading/trailing_empty_columns duerfen nicht negativ sein.")
        typen = (
            ("uhrzeit_spalten", self.uhrzeit_spalten),
            ("datum_spalten", self.datum_spalten),
            ("integer_spalten", self.integer_spalten),
            ("float_spalten", self.float_spalten),
            ("text_spalten", self.text_spalten),
        )
        for name_a, spalten_a in typen:
            set_a = set(spalten_a)
            for name_b, spalten_b in typen:
                if name_a >= name_b:
                    continue
                overlap = set_a & set(spalten_b)
                if overlap:
                    raise ValueError(
                        f"zeiteintrag_excel_export: Spalte(n) {sorted(overlap)} "
                        f"in {name_a} und {name_b} – nur ein Eintrag pro Spalte."
                    )


def _parse_farbwert(wert: Any, pfad: str) -> str:
    text = str(wert).strip()
    if not text.startswith("#") or len(text) not in (4, 7, 9):
        raise ValueError(f"{pfad}: Farbe muss als Hex (#RGB oder #RRGGBB) angegeben sein.")
    return text


def _section_mandanten(data: dict[str, Any]) -> tuple[Mandant, ...]:
    sec = data.get("mandanten")
    if sec is None:
        return ()
    if not isinstance(sec, dict):
        raise TypeError("[mandanten] muss eine Tabelle sein.")
    raw = sec.get("mandanten")
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise TypeError("[mandanten].mandanten muss eine Liste sein.")
    mandanten: list[Mandant] = []
    ids: set[int] = set()
    for idx, eintrag in enumerate(raw, start=1):
        if not isinstance(eintrag, dict):
            raise TypeError(f"mandanten.mandanten[{idx}] muss eine Tabelle sein.")
        pfad = f"mandanten.mandanten[{idx}]"
        if "name" not in eintrag or "id" not in eintrag:
            raise ValueError(f"{pfad}: name und id sind Pflichtfelder.")
        mandant_id = int(eintrag["id"])
        if mandant_id in ids:
            raise ValueError(f"{pfad}: id {mandant_id} ist bereits vergeben.")
        ids.add(mandant_id)
        fg_roh = eintrag.get("foreground_color", eintrag.get("farbe", "#000000"))
        bg_roh = eintrag.get("background_color", eintrag.get("hintergrundfarbe", "#FFFFFF"))
        rc_roh = eintrag.get("rowcounter_color", eintrag.get("zeilenzaehlerfarbe", "#000000"))
        mandanten.append(
            Mandant(
                name=str(eintrag["name"]).strip(),
                id=mandant_id,
                foreground_color=_parse_farbwert(fg_roh, f"{pfad}.foreground_color"),
                background_color=_parse_farbwert(bg_roh, f"{pfad}.background_color"),
                rowcounter_color=_parse_farbwert(rc_roh, f"{pfad}.rowcounter_color"),
            )
        )
    return tuple(mandanten)


@dataclass(frozen=True)
class AppConfig:
    name: str = "Taetigkeitsbericht"
    version: str = "0.0.0"
    mandanten: tuple[Mandant, ...] = ()
    wochenstunden_pro_mandant: dict[int, MandantWochenstunden] = field(default_factory=dict)
    wochenstunden_regel: float = 0.0
    wochenstunden_max: float = 0.0
    sollstunden_an_feiertagen: bool = False
    kommentar_urlaubstage: str = ""
    kommentar_krankheitstage: str = ""
    kommentar_urlaub_krank_modus: str = DEFAULT_KOMMENTAR_URLAUB_KRANK_MODUS
    kommentar_ueberstunden_frei: str = ""
    zeiteintrag_ausgeblendete_spalten: tuple[int, ...] = ()
    zeiteintrag_grauer_hintergrund_spalten: tuple[int, ...] = (
        DEFAULT_ZEITEINTRAG_GRAUER_HINTERGRUND_SPALTEN
    )
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
        uhrzeit_spalten=_parse_excel_spalten_indizes(
            sec.get("uhrzeit_spalten"),
            DEFAULT_ZEITEINTRAG_EXCEL_UHRZEIT_SPALTEN,
            "uhrzeit_spalten",
        ),
        datum_spalten=_parse_excel_spalten_indizes(
            sec.get("datum_spalten"),
            DEFAULT_ZEITEINTRAG_EXCEL_DATUM_SPALTEN,
            "datum_spalten",
        ),
        integer_spalten=_parse_excel_spalten_indizes(
            sec.get("integer_spalten"),
            DEFAULT_ZEITEINTRAG_EXCEL_INTEGER_SPALTEN,
            "integer_spalten",
        ),
        float_spalten=_parse_excel_spalten_indizes(
            sec.get("float_spalten"),
            DEFAULT_ZEITEINTRAG_EXCEL_FLOAT_SPALTEN,
            "float_spalten",
        ),
        text_spalten=_parse_excel_spalten_indizes(
            sec.get("text_spalten"),
            DEFAULT_ZEITEINTRAG_EXCEL_TEXT_SPALTEN,
            "text_spalten",
        ),
        html_formatierung=bool(sec.get("html_formatierung", True)),
    )


def load_zeiteintrag_excel_export_settings(
    config_path: Path | None = None,
) -> ZeiteintragExcelExportSettings:
    """Liest [zeiteintrag_excel_export] neu aus config.toml (z. B. vor jedem Export)."""
    if config_path is None:
        config_path = Path(__file__).resolve().parents[1] / "config.toml"
    if not config_path.is_file():
        return ZeiteintragExcelExportSettings()
    with config_path.open("rb") as f:
        data = tomllib.load(f)
    if not isinstance(data, dict):
        return ZeiteintragExcelExportSettings()
    return _section_zeiteintrag_excel_export(data)


def _parse_excel_spalten_indizes(
    raw: Any, default: tuple[int, ...], feldname: str
) -> tuple[int, ...]:
    if raw is None:
        return default
    return _parse_ausgeblendete_spalten(
        raw,
        ZEITEINTRAG_SPALTEN_MAX,
        f"zeiteintrag_excel_export.{feldname}",
    )


def _zeiteintrag_tabelle_section(data: dict[str, Any]) -> dict[str, Any]:
    sec = data.get("zeiteintrag_tabelle")
    if sec is None:
        return {}
    if not isinstance(sec, dict):
        raise TypeError("[zeiteintrag_tabelle] muss eine Tabelle sein.")
    return sec


def _section_zeiteintrag_ausgeblendete_spalten(data: dict[str, Any]) -> tuple[int, ...]:
    sec = _zeiteintrag_tabelle_section(data)
    return _parse_ausgeblendete_spalten(
        sec.get("ausgeblendete_spalten"),
        ZEITEINTRAG_SPALTEN_MAX,
        "zeiteintrag_tabelle.ausgeblendete_spalten",
    )


def _section_zeiteintrag_grauer_hintergrund_spalten(data: dict[str, Any]) -> tuple[int, ...]:
    sec = _zeiteintrag_tabelle_section(data)
    return _parse_spalten_indizes(
        sec.get("grauer_hintergrund_spalten"),
        ZEITEINTRAG_SPALTEN_MAX,
        "zeiteintrag_tabelle.grauer_hintergrund_spalten",
        default=DEFAULT_ZEITEINTRAG_GRAUER_HINTERGRUND_SPALTEN,
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


def _wochenstunden_section(data: dict[str, Any]) -> dict[str, Any]:
    sec = data.get("wochenstunden")
    return sec if isinstance(sec, dict) else {}


def _section_sollstunden_an_feiertagen(data: dict[str, Any]) -> bool:
    return bool(_sollstunden_section(data).get("sollstunden_an_feiertagen", False))


def _section_kommentar_urlaubstage(data: dict[str, Any]) -> str:
    wert = _sollstunden_section(data).get("kommentar_urlaubstage", "")
    return str(wert).strip() if wert is not None else ""


def _section_kommentar_krankheitstage(data: dict[str, Any]) -> str:
    wert = _sollstunden_section(data).get("kommentar_krankheitstage", "")
    return str(wert).strip() if wert is not None else ""


def _section_kommentar_urlaub_krank_modus(data: dict[str, Any]) -> str:
    sec = _wochenstunden_section(data)
    wert = sec.get(
        "kommentar_urlaub_krank_modus",
        _sollstunden_section(data).get(
            "kommentar_urlaub_krank_modus", DEFAULT_KOMMENTAR_URLAUB_KRANK_MODUS
        ),
    )
    modus = str(wert).strip().lower() if wert is not None else DEFAULT_KOMMENTAR_URLAUB_KRANK_MODUS
    if modus == "prefix":
        modus = "praefix"
    if modus not in KOMMENTAR_URLAUB_KRANK_MODI:
        return "kuerzel"
    return modus


def _section_wochenstunden_regel(data: dict[str, Any]) -> float:
    return float(_wochenstunden_section(data).get("wochenstunden_regel", 0) or 0)


def _section_wochenstunden_max(data: dict[str, Any]) -> float:
    return float(_wochenstunden_section(data).get("wochenstunden_max", 0) or 0)


def _section_kommentar_ueberstunden_frei(data: dict[str, Any]) -> str:
    wert = _sollstunden_section(data).get("kommentar_ueberstunden_frei", "")
    return str(wert).strip() if wert is not None else ""


def _parse_wochenstunden_liste(
    wochenstunden: list[Any], pfad_prefix: str
) -> dict[int, str]:
    out: dict[int, str] = {}
    for idx, eintrag in enumerate(wochenstunden, start=1):
        if not isinstance(eintrag, dict):
            raise TypeError(f"{pfad_prefix}[{idx}] muss eine Tabelle sein.")
        if "wochentag" not in eintrag or "stunden" not in eintrag:
            continue
        wt = int(eintrag["wochentag"])
        if not 1 <= wt <= 7:
            raise ValueError(f"{pfad_prefix}[{idx}].wochentag {wt} ungueltig (erwartet 1..7).")
        out[wt] = _stunden_zu_hh_mm(eintrag["stunden"])
    return out


def _parse_mandant_wochenstunden_gruppe(
    eintrag: dict[str, Any], pfad: str
) -> MandantWochenstunden:
    if "mandant_id" not in eintrag:
        raise ValueError(f"{pfad}: mandant_id ist Pflichtfeld.")
    mandant_id = int(eintrag["mandant_id"])
    raw_liste = eintrag.get("wochenstunden")
    if not isinstance(raw_liste, list):
        raise TypeError(f"{pfad}.wochenstunden muss eine Liste sein.")
    return MandantWochenstunden(
        mandant_id=mandant_id,
        soll_nach_vertrag_nach_wochentag=_parse_wochenstunden_liste(
            raw_liste, f"{pfad}.wochenstunden"
        ),
        wochenstunden_summe=float(eintrag.get("wochenstunden_summe", 0) or 0),
    )


def _section_wochenstunden_pro_mandant(
    data: dict[str, Any], mandanten: tuple[Mandant, ...]
) -> dict[int, MandantWochenstunden]:
    sec = _wochenstunden_section(data)
    gruppen = sec.get("mandant")
    ergebnis: dict[int, MandantWochenstunden] = {}

    if isinstance(gruppen, list):
        ids: set[int] = set()
        for idx, eintrag in enumerate(gruppen, start=1):
            if not isinstance(eintrag, dict):
                raise TypeError(f"wochenstunden.mandant[{idx}] muss eine Tabelle sein.")
            config = _parse_mandant_wochenstunden_gruppe(
                eintrag, f"wochenstunden.mandant[{idx}]"
            )
            if config.mandant_id in ids:
                raise ValueError(
                    f"wochenstunden.mandant[{idx}]: id {config.mandant_id} ist bereits vergeben."
                )
            ids.add(config.mandant_id)
            ergebnis[config.mandant_id] = config

    if not ergebnis:
        legacy = _sollstunden_section(data).get("wochenstunden")
        if isinstance(legacy, list) and mandanten:
            mapping = _parse_wochenstunden_liste(legacy, "sollstunden.wochenstunden")
            for mandant in mandanten:
                ergebnis[mandant.id] = MandantWochenstunden(
                    mandant_id=mandant.id,
                    soll_nach_vertrag_nach_wochentag=dict(mapping),
                )

    return ergebnis


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
    mandanten = _section_mandanten(data)
    return AppConfig(
        name=str(data.get("name", "Taetigkeitsbericht")),
        version=str(data.get("version", "0.0.0")),
        mandanten=mandanten,
        wochenstunden_pro_mandant=_section_wochenstunden_pro_mandant(data, mandanten),
        wochenstunden_regel=_section_wochenstunden_regel(data),
        wochenstunden_max=_section_wochenstunden_max(data),
        sollstunden_an_feiertagen=_section_sollstunden_an_feiertagen(data),
        kommentar_urlaubstage=_section_kommentar_urlaubstage(data),
        kommentar_krankheitstage=_section_kommentar_krankheitstage(data),
        kommentar_urlaub_krank_modus=_section_kommentar_urlaub_krank_modus(data),
        kommentar_ueberstunden_frei=_section_kommentar_ueberstunden_frei(data),
        zeiteintrag_ausgeblendete_spalten=_section_zeiteintrag_ausgeblendete_spalten(data),
        zeiteintrag_grauer_hintergrund_spalten=_section_zeiteintrag_grauer_hintergrund_spalten(
            data
        ),
        stundenplan_ausgeblendete_spalten=_section_stundenplan_tabelle(data),
        zeiteintrag_excel_export=_section_zeiteintrag_excel_export(data),
    )
