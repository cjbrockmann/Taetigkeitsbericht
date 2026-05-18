from __future__ import annotations

from External.Presentation.Desktop.zeiteintrag_excel_clipboard import (
    ExcelExportZelle,
    ExcelZelltyp,
    cell_spec_hat_platzhalter,
    datum_als_excel_serial,
    spreadsheetml_aus_excel_zeilen,
    tsv_zeile,
    uhrzeit_als_excel_serial,
    zellenwert_fuer_excel_tsv,
)


def test_uhrzeit_als_excel_serial():
    assert uhrzeit_als_excel_serial("12:00") == "0,5"


def test_datum_als_excel_serial():
    assert datum_als_excel_serial("01.01.2025") == "45658"


def test_tsv_zeile_join():
    zellen = [
        ExcelExportZelle(0, "a", "a", ExcelZelltyp.TEXT),
        ExcelExportZelle(1, "b", "b", ExcelZelltyp.TEXT),
    ]
    assert tsv_zeile(zellen) == "a\tb"


def test_cell_spec_hat_platzhalter():
    assert cell_spec_hat_platzhalter((1, None, 3)) is True
    assert cell_spec_hat_platzhalter((1, 2, 3)) is False


def test_spreadsheetml_blank_spalte_ss_index():
    zeilen = [
        [
            ExcelExportZelle(0, "1", "1", ExcelZelltyp.TEXT),
            ExcelExportZelle(None, "", "", ExcelZelltyp.BLANK),
            ExcelExportZelle(2, "3", "3", ExcelZelltyp.TEXT),
        ]
    ]
    xml = spreadsheetml_aus_excel_zeilen(zeilen, text_spalten=frozenset())
    assert 'ss:Index="1"' in xml
    assert 'ss:Index="3"' in xml
    assert xml.count("ss:Index=") == 2


def test_zellenwert_fuer_excel_tsv_uhrzeit():
    assert zellenwert_fuer_excel_tsv("08:00", ExcelZelltyp.UHRZEIT) != ""
