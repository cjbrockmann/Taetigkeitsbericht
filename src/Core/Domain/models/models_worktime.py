from __future__ import annotations

from datetime import date, time
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


class ArbeitszeitBasis(BaseModel):
    uhrzeit_von: time = Field(description="Startzeit")
    uhrzeit_bis: time = Field(description="Endzeit")
    pause_beginn:  Optional[time] = Field(default=None, description="Start der Unterbrechung")
    pause_ende:    Optional[time] = Field(default=None, description="Ende der Unterbrechung")
    pause2_beginn: Optional[time] = Field(default=None, description="Start der zweiten Unterbrechung")
    pause2_ende:   Optional[time] = Field(default=None, description="Ende der zweiten Unterbrechung")
    anmerkung:     Optional[str]  = Field(default=None, max_length=80)

    @staticmethod
    def _zeit_im_arbeitszeitfenster(zeit: time, uhrzeit_von: time, uhrzeit_bis: time) -> bool:
        return uhrzeit_von <= zeit <= uhrzeit_bis

    def _pruefe_pause_einzelzeit(
        self,
        zeit: time | None,
        feldname: str,
        uhrzeit_von: time,
        uhrzeit_bis: time,
    ) -> None:
        if zeit is None:
            return
        if not self._zeit_im_arbeitszeitfenster(zeit, uhrzeit_von, uhrzeit_bis):
            raise ValueError(
                f"{feldname} muss zwischen uhrzeit_von und uhrzeit_bis liegen."
            )

    @staticmethod
    def _pausen_intervalle_ueberlappen(
        beginn_a: time,
        ende_a: time,
        beginn_b: time,
        ende_b: time,
    ) -> bool:
        return beginn_a < ende_b and beginn_b < ende_a

    def _hat_gesetzte_pause(self) -> bool:
        return any(
            (
                self.pause_beginn,
                self.pause_ende,
                self.pause2_beginn,
                self.pause2_ende,
            )
        )

    @model_validator(mode="after")
    def pruefe_zeitraeume(self) -> "ArbeitszeitBasis":
        if self.uhrzeit_von is not None and self.uhrzeit_bis is not None:
            if self.uhrzeit_von > self.uhrzeit_bis:
                raise ValueError(
                    "uhrzeit_von darf nicht nach uhrzeit_bis liegen."
                )

            if self.uhrzeit_von == self.uhrzeit_bis and self._hat_gesetzte_pause():
                raise ValueError(
                    "Bei gleicher Arbeitszeit (uhrzeit_von = uhrzeit_bis) "
                    "dürfen keine Pausen gesetzt sein."
                )

            for feldname, zeit in (
                ("pause_beginn", self.pause_beginn),
                ("pause_ende", self.pause_ende),
                ("pause2_beginn", self.pause2_beginn),
                ("pause2_ende", self.pause2_ende),
            ):
                self._pruefe_pause_einzelzeit(
                    zeit, feldname, self.uhrzeit_von, self.uhrzeit_bis
                )

        if (self.pause_beginn is None) ^ (self.pause_ende is None):
            raise ValueError("pause_beginn und pause_ende müssen gemeinsam gesetzt sein.")

        if self.pause_beginn and self.pause_ende:
            if self.pause_beginn >= self.pause_ende:
                raise ValueError("pause_beginn muss vor pause_ende liegen.")

        if (self.pause2_beginn is None) ^ (self.pause2_ende is None):
            raise ValueError("pause2_beginn und pause2_ende müssen gemeinsam gesetzt sein.")

        if self.pause2_beginn and self.pause2_ende:
            if self.pause2_beginn >= self.pause2_ende:
                raise ValueError("pause2_beginn muss vor pause2_ende liegen.")

        if (
            self.pause_beginn
            and self.pause_ende
            and self.pause2_beginn
            and self.pause2_ende
            and self._pausen_intervalle_ueberlappen(
                self.pause_beginn,
                self.pause_ende,
                self.pause2_beginn,
                self.pause2_ende,
            )
        ):
            raise ValueError("Pause 1 und Pause 2 dürfen sich nicht überlappen.")

        return self


# Hauptmodell für Zeiteinträge, das in der Datenbank gespeichert wird
class Zeiteintrag(ArbeitszeitBasis):
    id: Optional[UUID] = None
    datum: date

# Klasse, die an die GUI übergeben wird, mit zusätzlichen Feldern für die Anzeige und Bearbeitung
class ZeiteintragsDTO(Zeiteintrag):
    uhrzeit_von: Optional[time] = Field(description="Startzeit", default=None)  # Typ‑Override
    uhrzeit_bis: Optional[time] = Field(description="Endzeit", default=None)    # Typ‑Override
    geleistete_stunden: Optional[time] = Field(description="Endzeit", default=None)
    soll_stunden_nach_Stundenplan: Optional[time] = Field(description="Soll-Stunden nach Stundenplan", default=None)
    soll_stunden_nach_vertrag: Optional[time] = Field(description="Soll-Stunden nach Vertrag", default=None)
    ist_urlaub: bool = Field(description="Ist Urlaub", default=False)
    ist_krank: bool = Field(description="Ist Krank", default=False)
    ist_feiertag: bool = Field(description="Ist Feiertag", default=False)
    ist_ferien: bool = Field(description="Ist Ferien", default=False)
    ist_betriebsferien: bool = Field(description="Ist Betriebsferien", default=False) 
    feiertagsname: Optional[str] = Field(default=None, max_length=80, description="Name des Feiertags")
    schulferienname: Optional[str] = Field(default=None, max_length=80, description="Name der Schulferien")
    anmerkung_kurz: Optional[str] = Field(
        default=None,
        max_length=80,
        description="Kurzkommentar nur fuer Anzeige/Excel, nicht persistiert",
    )

    @model_validator(mode="after")
    def pruefe_zeitraeume(self) -> "ZeiteintragsDTO":
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


# Klasse für den Stundenplan, der eine Vorlage für die Soll-Arbeitszeiten an jedem Wochentag darstellt
class Stundenplan(ArbeitszeitBasis):
    id: Optional[int] = None
    wochentag: int = Field(ge=1, le=7, description="1=Montag, 7=Sonntag")




# -------------------------------------------------------------------------------
# Weitere Modelle für Stundenplan, Feiertage, usw.


class Feiertag(BaseModel):
    datum: date
    feiertagsname: str = Field(max_length=80, description="Name des Feiertags")
    hinweis: Optional[str] = Field(default=None, max_length=80, description="Zusatzinfo, z. B. aus Feiertags-API")
    ist_halber_tag: bool = Field(
        default=False, description="True = halber Feiertag, False = ganzer Feiertag"
    )
    ist_offiziell: bool = Field(
        default=True, description="True = gesetzlicher/offizieller Feiertag"
    )

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
        