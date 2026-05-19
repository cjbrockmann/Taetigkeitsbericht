from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from App.app_config import Mandant


class MandantAuswahl(QObject):
    """
    Globale Mandantenauswahl der laufenden Sitzung.
    Die aktuelle ID liegt in ``mandant_id``; Zugriff z. B. via ``MandantAuswahl.instance()``.
  """

    mandant_id_geaendert = Signal(int)

    _instance: MandantAuswahl | None = None

    def __init__(self, mandanten: tuple[Mandant, ...]) -> None:
        super().__init__()
        if not mandanten:
            raise ValueError("mandanten: mindestens ein Eintrag in config.toml erforderlich.")
        self._mandanten = mandanten
        self._mandant_id = mandanten[0].id
        MandantAuswahl._instance = self

    @classmethod
    def instance(cls) -> MandantAuswahl:
        if cls._instance is None:
            raise RuntimeError(
                "MandantAuswahl ist noch nicht initialisiert (App-Start / DI)."
            )
        return cls._instance

    @property
    def mandanten(self) -> tuple[Mandant, ...]:
        return self._mandanten

    @property
    def mandant_id(self) -> int:
        """Globale Mandanten-ID (nach bestaetigtem Wechsel in der Combobox)."""
        return self._mandant_id

    def aktueller_mandant(self) -> Mandant:
        mandant = self.mandant_nach_id(self._mandant_id)
        return mandant if mandant is not None else self._mandanten[0]

    def mandant_nach_id(self, mandant_id: int) -> Mandant | None:
        for mandant in self._mandanten:
            if mandant.id == mandant_id:
                return mandant
        return None

    def set_mandant_id(self, mandant_id: int) -> None:
        if mandant_id == self._mandant_id:
            return
        if self.mandant_nach_id(mandant_id) is None:
            return
        self._mandant_id = mandant_id
        self.mandant_id_geaendert.emit(mandant_id)
