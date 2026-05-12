"""Gemeinsames QTableView-Stylesheet fuer alle Desktop-Tabellen."""

STANDARD_TABLE_VIEW_STYLESHEET = (
    "QTableView::item:hover:!selected {"
    "background-color: #ececec;"
    "color: #000000;"
    "}"
    "QTableView::item:selected:hover {"
    "background-color: #fff9c4;"
    "color: #000000;"
    "}"
    "QTableView::item:selected {"
    "background-color: #fff9c4;"
    "color: #000000;"
    "}"
    "QTableView::item:selected:active {"
    "color: #000000;"
    "}"
    "QTableView::item:selected:!active {"
    "background-color: #fff9c4;"
    "color: #000000;"
    "}"
)

# Kein erzwungenes color bei :selected, damit Delegate/Modell die Schriftfarbe setzen koennen
# (ungespeicherte Zeilen rot, auch wenn markiert).
ZEITEINTRAG_TABLE_VIEW_STYLESHEET = (
    "QTableView::item:hover:!selected {"
    "background-color: #ececec;"
    "}"
    "QTableView::item:selected:hover {"
    "background-color: #fff9c4;"
    "}"
    "QTableView::item:selected {"
    "background-color: #fff9c4;"
    "}"
    "QTableView::item:selected:!active {"
    "background-color: #fff9c4;"
    "}"
)
