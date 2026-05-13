from __future__ import annotations

from datetime import date, time
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


class ArbeitszeitBasis(BaseModel):
    uhrzeit_von: time = Field(description="Startzeit")
    uhrzeit_bis: time = Field(description="Endzeit")
    pause_beginn: Optional[time] = Field(default=None, description="Start der Unterbrechung")
    pause_ende: Optional[time] = Field(default=None, description="Ende der Unterbrechung")
    pause2_beginn: Optional[time] = Field(default=None, description="Start der zweiten Unterbrechung")
    pause2_ende: Optional[time] = Field(default=None, description="Ende der zweiten Unterbrechung")
    anmerkung: Optional[str] = Field(default=None, max_length=80)

    @model_validator(mode="after")
    def pruefe_zeitraeume(self) -> "ArbeitszeitBasis":
        if self.uhrzeit_von >= self.uhrzeit_bis:
            raise ValueError("uhrzeit_von muss vor uhrzeit_bis liegen.")

        if (self.pause_beginn is None) ^ (self.pause_ende is None):
            raise ValueError("pause_beginn und pause_ende muessen gemeinsam gesetzt sein.")

        if self.pause_beginn and self.pause_ende:
            if self.pause_beginn >= self.pause_ende:
                raise ValueError("pause_beginn muss vor pause_ende liegen.")
            if self.pause_beginn < self.uhrzeit_von or self.pause_ende > self.uhrzeit_bis:
                raise ValueError("Unterbrechung muss innerhalb der Arbeitszeit liegen.")

        if (self.pause2_beginn is None) ^ (self.pause2_ende is None):
            raise ValueError("pause2_beginn und pause2_ende muessen gemeinsam gesetzt sein.")

        if self.pause2_beginn and self.pause2_ende:
            if self.pause2_beginn >= self.pause2_ende:
                raise ValueError("pause2_beginn muss vor pause2_ende liegen.")
            if self.pause2_beginn < self.uhrzeit_von or self.pause2_ende > self.uhrzeit_bis:
                raise ValueError("Die zweite Unterbrechung muss innerhalb der Arbeitszeit liegen.")

        return self


class Zeiteintrag(ArbeitszeitBasis):
    id: Optional[UUID] = None
    datum: date


class Stundenplan(ArbeitszeitBasis):
    id: Optional[int] = None
    wochentag: int = Field(ge=1, le=7, description="1=Montag, 7=Sonntag")


class Feiertag(BaseModel):
    datum: date
    feiertagsname: str = Field(max_length=80, description="Name des Feiertags")
    hinweis: Optional[str] = Field(default=None, max_length=80, description="Zusatzinfo, z. B. aus Feiertags-API")

# Klasse zum Lesen der Einträge aus der Datenbank
class ZeiteintragsDTO(Zeiteintrag):
    geleistete_stunden: time = Field(description="Endzeit")
    soll_stunden_nach_Stundenplan: time = Field(description="Soll-Stunden nach Stundenplan")
    soll_stunden_nach_vertrag: time = Field(description="Soll-Stunden nach Vertrag")
    ist_urlaub: bool = Field(description="Ist Urlaub")
    ist_krank: bool = Field(description="Ist Krank")
    ist_feiertag: bool = Field(description="Ist Feiertag")
    ist_ferien: bool = Field(description="Ist Ferien")
    ist_betriebsferien: bool = Field(description="Ist Betriebsferien") 

class Urlaubsantrag(BaseModel):
    id: Optional[int] = None
    datum_von: date = Field(description="Datum von")
    datum_bis: date = Field(description="Datum bis")
    urlaubstyp: str = Field(description="Urlaubstyp", max_length=80)
    urlaubstage: float = Field(description="Urlaubstage", ge=0)
    genehmigt: bool = Field(default=False, description="Genehmigt")

    @field_validator("urlaubstage")
    @classmethod
    def urlaubstage_nur_halbe_tage(cls, v: float) -> float:
        doppelt = v * 2
        if abs(doppelt - round(doppelt)) > 1e-6:
            raise ValueError(
                "Urlaubstage nur in Halbtags-Schritten (z. B. 1, 1.5, 2, 2.5)."
            )
        return v

    @model_validator(mode="after")
    def pruefe_datumsbereich(self) -> "Urlaubsantrag":
        if self.datum_von > self.datum_bis:
            raise ValueError("datum_von muss vor oder gleich datum_bis liegen.")
        return self

class Krankmeldung(BaseModel):
    id: Optional[int] = None
    krank_von: date = Field(description="Krank von")
    krank_bis: date = Field(description="Krank bis")
    krankmeldungstage: int = Field(description="Krankmeldungstage", ge=0)
    anmerkung: Optional[str] = Field(default=None, max_length=80)

    @model_validator(mode="after")
    def pruefe_datumsbereich(self) -> "Krankmeldung":
        if self.krank_von > self.krank_bis:
            raise ValueError("krank_von muss vor oder gleich krank_bis liegen.")
        return self

class Betriebsferien(BaseModel):
    id: Optional[int] = None
    datum_von: date = Field(description="Datum von")
    datum_bis: date = Field(description="Datum bis")
    betriebsferienname: str = Field(description="Betriebsferienname", max_length=80)
    anmerkung: Optional[str] = Field(default=None, max_length=80)

    @model_validator(mode="after")
    def pruefe_datumsbereich(self) -> "Betriebsferien":
        if self.datum_von > self.datum_bis:
            raise ValueError("datum_von muss vor oder gleich datum_bis liegen.")
        return self

class Schulferien(BaseModel):
    id: Optional[int] = None
    datum_von: date = Field(description="Datum von")
    datum_bis: date = Field(description="Datum bis")
    schulferienname: str = Field(description="Schulferienname", max_length=80)
    anmerkung: Optional[str] = Field(default=None, max_length=80)

    @model_validator(mode="after")
    def pruefe_datumsbereich(self) -> "Schulferien":
        if self.datum_von > self.datum_bis:
            raise ValueError("datum_von muss vor oder gleich datum_bis liegen.")
        return self
        