from __future__ import annotations

from datetime import time
from typing import Optional

from pydantic import Field, model_validator

from .arbeitszeit_basis import ArbeitszeitBasis
from .zeiteintrag import Zeiteintrag


class ZeiteintragsDTO(Zeiteintrag):
    uhrzeit_von: Optional[time] = Field(description="Startzeit", default=None)
    uhrzeit_bis: Optional[time] = Field(description="Endzeit", default=None)
    geleistete_stunden: Optional[time] = Field(description="Endzeit", default=None)
    soll_stunden_nach_Stundenplan: Optional[time] = Field(
        description="Soll-Stunden nach Stundenplan", default=None
    )
    soll_stunden_nach_vertrag: Optional[time] = Field(
        description="Soll-Stunden nach Vertrag", default=None
    )
    ist_urlaub: bool = Field(description="Ist Urlaub", default=False)
    ist_krank: bool = Field(description="Ist Krank", default=False)
    ist_feiertag: bool = Field(description="Ist Feiertag", default=False)
    ist_ferien: bool = Field(description="Ist Ferien", default=False)
    ist_betriebsferien: bool = Field(description="Ist Betriebsferien", default=False)
    feiertagsname: Optional[str] = Field(
        default=None, max_length=80, description="Name des Feiertags"
    )
    schulferienname: Optional[str] = Field(
        default=None, max_length=80, description="Name der Schulferien"
    )
    info: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Stundenplan-Kommentar (nur Anzeige, nicht persistiert)",
    )

    @model_validator(mode="after")
    def pruefe_zeitraeume(self) -> ZeiteintragsDTO:
        """Weniger streng als Zeiteintrag: unvollstaendige und Ueberstunden-frei-Zeilen."""
        if self.uhrzeit_von is None or self.uhrzeit_bis is None:
            return self
        if self.uhrzeit_von == self.uhrzeit_bis:
            return self
        if (self.pause_beginn is None) ^ (self.pause_ende is None):
            return self
        if (self.pause2_beginn is None) ^ (self.pause2_ende is None):
            return self
        return ArbeitszeitBasis.pruefe_zeitraeume(self)
