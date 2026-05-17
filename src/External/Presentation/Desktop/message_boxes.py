"""Deutsche Beschriftung fuer QMessageBox-Dialoge (Ja/Nein, OK)."""

from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QWidget


def _setze_ja_nein_texte(box: QMessageBox) -> None:
    ja = box.button(QMessageBox.StandardButton.Yes)
    nein = box.button(QMessageBox.StandardButton.No)
    if ja is not None:
        ja.setText("Ja")
    if nein is not None:
        nein.setText("Nein")


def frage_ja_nein(
    parent: QWidget | None,
    titel: str,
    text: str,
    *,
    standard_nein: bool = True,
) -> bool:
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Icon.Question)
    box.setWindowTitle(titel)
    box.setText(text)
    box.setStandardButtons(
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    box.setDefaultButton(
        QMessageBox.StandardButton.No
        if standard_nein
        else QMessageBox.StandardButton.Yes
    )
    _setze_ja_nein_texte(box)
    return box.exec() == QMessageBox.StandardButton.Yes


def warnung(parent: QWidget | None, titel: str, text: str) -> None:
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Icon.Warning)
    box.setWindowTitle(titel)
    box.setText(text)
    box.setStandardButtons(QMessageBox.StandardButton.Ok)
    ok = box.button(QMessageBox.StandardButton.Ok)
    if ok is not None:
        ok.setText("OK")
    box.exec()
