"""Hilfen fuer „Fuer Excel kopieren“ (TSV + optional Spreadsheet-XML)."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from html import escape
from xml.sax.saxutils import escape as xml_escape

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
    BLANK = "blank"  # cell_spec „blank“: Spalte beim Einfuegen nicht ueberschreiben (SpreadsheetML)


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


def _tsv_feld(
    zelle: ExcelExportZelle, *, leere_als_leerzeichen: bool
) -> str:
    """BLANK unveraendert; bei reinem TSV-Export leere Felder als „ “ zum Ueberschreiben in Excel."""
    if zelle.typ == ExcelZelltyp.BLANK:
        return zelle.text
    if leere_als_leerzeichen and not zelle.text.strip():
        return " "
    return zelle.text


def tsv_zeile(
    zeilen_zellen: list[ExcelExportZelle], *, leere_als_leerzeichen: bool = False
) -> str:
    return "\t".join(
        _tsv_feld(z, leere_als_leerzeichen=leere_als_leerzeichen) for z in zeilen_zellen
    )


def _export_zelle_hat_inhalt(zelle: ExcelExportZelle) -> bool:
    if zelle.typ == ExcelZelltyp.BLANK:
        return False
    return bool(zelle.text.strip() or zelle.anzeige.strip())


def _spreadsheetml_datentyp_und_wert(
    zelle: ExcelExportZelle, *, text_spalten: frozenset[int]
) -> tuple[str, str] | None:
    """(data_type, wert) oder None bei BLANK. Keine Styles — Excel-Rahmen bleiben erhalten."""
    if zelle.typ == ExcelZelltyp.BLANK:
        return None
    if zelle.quell_spalte in text_spalten or zelle.typ == ExcelZelltyp.TEXT:
        return "String", "" if not _export_zelle_hat_inhalt(zelle) else zelle.anzeige
    if not _export_zelle_hat_inhalt(zelle):
        return "String", ""
    match zelle.typ:
        case ExcelZelltyp.UHRZEIT | ExcelZelltyp.DATUM | ExcelZelltyp.FLOAT:
            serial = zelle.text.strip().replace(",", ".")
            return "Number", serial
        case ExcelZelltyp.INTEGER:
            return "Number", zelle.text.strip()
        case _:
            return "String", zelle.anzeige


def _spreadsheetml_cell_xml(
    spalte: int, zelle: ExcelExportZelle, *, text_spalten: frozenset[int]
) -> str | None:
    """Eine Zelle fuer SpreadsheetML; None = BLANK (Spalte ueberspringen)."""
    daten = _spreadsheetml_datentyp_und_wert(zelle, text_spalten=text_spalten)
    if daten is None:
        return None
    typ, wert = daten
    return (
        f'<Cell ss:Index="{spalte}"><Data ss:Type="{typ}">'
        f"{xml_escape(wert)}</Data></Cell>"
    )


def _spreadsheetml_spaltenanzahl(zeilen: list[list[ExcelExportZelle]]) -> int:
    if not zeilen:
        return 1
    return max(len(zellen) for zellen in zeilen)


def spreadsheetml_aus_excel_zeilen(
    zeilen: list[list[ExcelExportZelle]],
    *,
    text_spalten: frozenset[int],
) -> str:
    """Excel-XML mit ss:Index: BLANK-Spalten fehlen, nur Werte (ohne Zellstyles)."""
    zeilen_xml: list[str] = []
    for zellen in zeilen:
        zellen_xml: list[str] = []
        spalte = 1
        for zelle in zellen:
            zell_xml = _spreadsheetml_cell_xml(spalte, zelle, text_spalten=text_spalten)
            if zell_xml is None:
                if zelle.typ == ExcelZelltyp.BLANK:
                    spalte += 1
                continue
            zellen_xml.append(zell_xml)
            spalte += 1
        zeilen_xml.append(f"<Row>{''.join(zellen_xml)}</Row>")
    spalten = _spreadsheetml_spaltenanzahl(zeilen)
    zeilen_anzahl = len(zeilen)
    return (
        '<?xml version="1.0"?>\n'
        '<?mso-application progid="Excel.Sheet"?>\n'
        '<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"\n'
        ' xmlns:o="urn:schemas-microsoft-com:office:office"\n'
        ' xmlns:x="urn:schemas-microsoft-com:office:excel"\n'
        ' xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet"\n'
        ' xmlns:html="http://www.w3.org/TR/REC-html40">\n'
        '<Worksheet ss:Name="Zeiteintraege">\n'
        f'<Table ss:ExpandedColumnCount="{spalten}" ss:ExpandedRowCount="{zeilen_anzahl}">\n'
        f"{''.join(zeilen_xml)}\n"
        "</Table></Worksheet></Workbook>"
    )


def _windows_zwischenablage_xml_spreadsheet_hinzufuegen(xml: str) -> bool:
    """
    Format „XML Spreadsheet“ zur bestehenden Zwischenablage hinzufuegen (ohne EmptyClipboard).
    So bleiben TSV/HTML von Qt erhalten (LibreOffice/OpenOffice Calc) und Excel kann ss:Index nutzen.
    """
    if sys.platform != "win32":
        return False
    import ctypes

    gmem_moveable = 0x0002
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    fmt = user32.RegisterClipboardFormatW("XML Spreadsheet")
    if fmt == 0:
        return False

    payload = xml.encode("utf-8")
    if not user32.OpenClipboard(None):
        return False
    try:
        h_mem = kernel32.GlobalAlloc(gmem_moveable, len(payload))
        if not h_mem:
            return False
        ptr = kernel32.GlobalLock(h_mem)
        if not ptr:
            kernel32.GlobalFree(h_mem)
            return False
        ctypes.memmove(ptr, payload, len(payload))
        kernel32.GlobalUnlock(h_mem)
        if not user32.SetClipboardData(fmt, h_mem):
            kernel32.GlobalFree(h_mem)
            return False
        return True
    finally:
        user32.CloseClipboard()


def zwischenablage_format_hinweis(formate: frozenset[str]) -> str:
    """Lesbarer Formatname fuer die Statuszeile (entspricht zwischenablage_excel_formate)."""
    if "xml" in formate:
        return "TSV + Spreadsheet-XML"
    return "TSV"


def zwischenablage_excel_formate(*, spreadsheet_xml_formatierung: bool) -> frozenset[str]:
    """
    Welche Formate setze_excel_zwischenablage erzeugt (immer „tsv“).

    spreadsheet_xml_formatierung=false: nur TSV.
    spreadsheet_xml_formatierung=true: TSV + Spreadsheet-XML (ss:Index bei blank-Zellen).
    """
    formate: set[str] = {"tsv"}
    if spreadsheet_xml_formatierung:
        formate.add("xml")
    return frozenset(formate)


def setze_excel_zwischenablage(
    zeilen: list[list[ExcelExportZelle]],
    *,
    text_spalten: frozenset[int],
    spreadsheet_xml_formatierung: bool,
    kopfzeile: bool = False,
) -> tuple[bool, frozenset[str]]:
    """
    Zwischenablage fuer Excel und LibreOffice/OpenOffice Calc.

    Gibt (erfolg, formate) zurueck; formate fuer die Statuszeile (siehe
    zwischenablage_format_hinweis).
    """
    from PySide6.QtCore import QByteArray, QMimeData
    from PySide6.QtGui import QGuiApplication

    formate = zwischenablage_excel_formate(
        spreadsheet_xml_formatierung=spreadsheet_xml_formatierung,
    )
    leere_als_leerzeichen = formate == frozenset({"tsv"})

    tsv = "\n".join(
        tsv_zeile(row, leere_als_leerzeichen=leere_als_leerzeichen) for row in zeilen
    )
    mime = QMimeData()
    mime.setText(tsv)

    xml: str | None = None
    if "xml" in formate:
        xml = spreadsheetml_aus_excel_zeilen(zeilen, text_spalten=text_spalten)
        raw = QByteArray(xml.encode("utf-8"))
        for name in ("XML Spreadsheet", "application/vnd.ms-excel", "text/xml"):
            mime.setData(name, raw)

    cb = QGuiApplication.clipboard()
    if cb is None:
        return False, formate
    cb.setMimeData(mime)
    if xml is not None:
        _windows_zwischenablage_xml_spreadsheet_hinzufuegen(xml)
    return cb.mimeData() is not None, formate
