"""Hilfen fuer „Fuer Excel kopieren“ (TSV + optional HTML mit Excel-Zahlformaten)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from html import escape

from External.Presentation.Desktop.arbeitszeit_berechnung import zeit_aus_text

_EXCEL_EPOCH = date(1899, 12, 30)
_EXCEL_UHRZEIT_FORMAT = "hh:mm:ss"
_EXCEL_DATUM_FORMAT = "dd\\.mm\\.yyyy"
_EXCEL_INTEGER_FORMAT = "0"
_EXCEL_FLOAT_FORMAT = "0.00"
_EXCEL_TEXT_FORMAT = "@"


class ExcelZelltyp(str, Enum):
    TEXT = "text"
    UHRZEIT = "uhrzeit"
    DATUM = "datum"
    INTEGER = "integer"
    FLOAT = "float"
    BLANK = "blank"  # cell_spec „blank“: Platzhalter, Excel-Zelle nicht ueberschreiben


@dataclass(frozen=True)
class ExcelExportZelle:
    """Eine Ausgabezelle in cell_spec-Reihenfolge."""

    quell_spalte: int | None
    text: str  # TSV (Excel-Serienzahlen fuer Datum/Uhrzeit)
    anzeige: str  # HTML-Anzeige (HH:MM:SS, DD.MM.YYYY, …)
    typ: ExcelZelltyp


def excel_zelltyp_fuer_spalte(
    spalte: int | None,
    *,
    uhrzeit_spalten: frozenset[int],
    datum_spalten: frozenset[int],
    integer_spalten: frozenset[int],
    float_spalten: frozenset[int],
) -> ExcelZelltyp:
    if spalte is None:
        return ExcelZelltyp.TEXT
    if spalte in uhrzeit_spalten:
        return ExcelZelltyp.UHRZEIT
    if spalte in datum_spalten:
        return ExcelZelltyp.DATUM
    if spalte in integer_spalten:
        return ExcelZelltyp.INTEGER
    if spalte in float_spalten:
        return ExcelZelltyp.FLOAT
    return ExcelZelltyp.TEXT


def _float_mit_deutschem_komma(wert: float) -> str:
    s = format(wert, ".15g")
    if "e" in s.lower():
        s = format(wert, "f")
    return s.replace(".", ",")


def uhrzeit_als_excel_text(roh: str) -> str:
    """Anzeige fuer HTML (HH:MM:SS)."""
    t = zeit_aus_text(roh.strip())
    if t is None:
        return ""
    return t.strftime("%H:%M:%S")


def uhrzeit_als_excel_serial(roh: str) -> str:
    """Bruchteil eines Tages — Excel-Datentyp Uhrzeit beim TSV-Einfuegen."""
    t = zeit_aus_text(roh.strip())
    if t is None:
        return ""
    sekunden = t.hour * 3600 + t.minute * 60 + t.second
    return _float_mit_deutschem_komma(sekunden / 86400)


def datum_als_excel_text(roh: str) -> str:
    text = roh.strip()
    if not text:
        return ""
    try:
        datum = datetime.strptime(text, "%d.%m.%Y").date()
    except ValueError:
        return ""
    return datum.strftime("%d.%m.%Y")


def datum_als_excel_serial(roh: str) -> str:
    """Tageszahl seit 30.12.1899 — Excel-Datentyp Datum beim TSV-Einfuegen."""
    text = roh.strip()
    if not text:
        return ""
    try:
        datum = datetime.strptime(text, "%d.%m.%Y").date()
    except ValueError:
        return ""
    return str((datum - _EXCEL_EPOCH).days)


def integer_als_excel_text(roh: str) -> str:
    text = roh.strip()
    if not text:
        return ""
    try:
        return str(int(text.replace(" ", "")))
    except ValueError:
        return ""


def float_als_excel_text(roh: str) -> str:
    text = roh.strip().replace(" ", "").replace(",", ".")
    if not text:
        return ""
    try:
        wert = float(text)
    except ValueError:
        return ""
    return _float_mit_deutschem_komma(wert)


def zellenwert_fuer_excel_tsv(roh: str, typ: ExcelZelltyp) -> str:
    """Werte fuer text/plain (TSV): Zahlformate, die Excel als Datum/Uhrzeit/Zahl erkennt."""
    match typ:
        case ExcelZelltyp.UHRZEIT:
            return uhrzeit_als_excel_serial(roh)
        case ExcelZelltyp.DATUM:
            return datum_als_excel_serial(roh)
        case ExcelZelltyp.INTEGER:
            return integer_als_excel_text(roh)
        case ExcelZelltyp.FLOAT:
            return float_als_excel_text(roh)
        case _:
            return roh


def zellenwert_fuer_excel_anzeige(roh: str, typ: ExcelZelltyp) -> str:
    """Lesbare Werte fuer HTML (zusammen mit mso-number-format)."""
    match typ:
        case ExcelZelltyp.UHRZEIT:
            return uhrzeit_als_excel_text(roh)
        case ExcelZelltyp.DATUM:
            return datum_als_excel_text(roh)
        case ExcelZelltyp.INTEGER:
            return integer_als_excel_text(roh)
        case ExcelZelltyp.FLOAT:
            return float_als_excel_text(roh)
        case _:
            return roh


def zellenwerte_fuer_excel(roh: str, typ: ExcelZelltyp) -> tuple[str, str]:
    return zellenwert_fuer_excel_tsv(roh, typ), zellenwert_fuer_excel_anzeige(roh, typ)


def cell_spec_hat_platzhalter(cell_spec: tuple[int | None, ...]) -> bool:
    return any(spec is None for spec in cell_spec)


def html_td_fuer_excel(zelle: ExcelExportZelle, *, ist_kopfzeile: bool, text_spalten: frozenset[int]) -> str:
    if zelle.typ == ExcelZelltyp.BLANK:
        return "<td></td>"
    if ist_kopfzeile:
        return f"<td>{escape(zelle.anzeige)}</td>"
    if zelle.quell_spalte in text_spalten:
        return (
            f'<td style="mso-number-format:&quot;{_EXCEL_TEXT_FORMAT}&quot;">'
            f"{escape(zelle.anzeige)}</td>"
        )
    if zelle.typ == ExcelZelltyp.TEXT:
        return f"<td>{escape(zelle.anzeige)}</td>"
    if not zelle.anzeige:
        return "<td></td>"

    match zelle.typ:
        case ExcelZelltyp.UHRZEIT:
            fmt = _EXCEL_UHRZEIT_FORMAT
        case ExcelZelltyp.DATUM:
            fmt = _EXCEL_DATUM_FORMAT
        case ExcelZelltyp.INTEGER:
            fmt = _EXCEL_INTEGER_FORMAT
        case ExcelZelltyp.FLOAT:
            fmt = _EXCEL_FLOAT_FORMAT
        case _:
            return f"<td>{escape(zelle.anzeige)}</td>"

    return (
        f'<td style="mso-number-format:&quot;{fmt}&quot;">'
        f"{escape(zelle.anzeige)}</td>"
    )


def html_tabelle_fuer_excel(
    zeilen: list[list[ExcelExportZelle]],
    *,
    text_spalten: frozenset[int],
    kopfzeile: bool,
) -> str:
    """HTML-Tabelle in derselben Spaltenreihenfolge wie cell_spec (TSV)."""
    body_rows: list[str] = []
    for row_idx, zellen in enumerate(zeilen):
        ist_kopf = kopfzeile and row_idx == 0
        tds = [html_td_fuer_excel(z, ist_kopfzeile=ist_kopf, text_spalten=text_spalten) for z in zellen]
        body_rows.append(f"<tr>{''.join(tds)}</tr>")
    return (
        "<html><head><meta charset='utf-8'></head>"
        f"<body><table>{''.join(body_rows)}</table></body></html>"
    )


def tsv_zeile(zeilen_zellen: list[ExcelExportZelle]) -> str:
    return "\t".join(z.text for z in zeilen_zellen)
