from __future__ import annotations

import sys
from pathlib import Path

# Erlaubt direkten Start dieser Datei ohne gesetztes PYTHONPATH.
SRC_ROOT = Path(__file__).resolve().parents[3]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from PySide6.QtCore import QLocale
from PySide6.QtWidgets import QApplication

from App.bootstrap import create_injector
from External.Presentation.Desktop.zeiteintrag_window import ZeiteintragWindow


def main() -> int:
    QLocale.setDefault(QLocale(QLocale.Language.German, QLocale.Country.Germany))
    app = QApplication(sys.argv)

    injector = create_injector()
    window = injector.get(ZeiteintragWindow)
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
