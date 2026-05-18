from __future__ import annotations

from datetime import date, time
from typing import Optional

from sqlalchemy import Column, String
from sqlmodel import Field, SQLModel


class ZeiteintragTable(SQLModel, table=True):
    __tablename__ = "zeiteintrag"

    id: str = Field(sa_column=Column(String(36), primary_key=True))
    mandant_id: int
    datum: date
    uhrzeit_von: time
    uhrzeit_bis: time
    pause_beginn: Optional[time] = None
    pause_ende: Optional[time] = None
    pause2_beginn: Optional[time] = None
    pause2_ende: Optional[time] = None
    anmerkung: Optional[str] = Field(default=None, max_length=80)


class StundenplanTable(SQLModel, table=True):
    __tablename__ = "stundenplan"

    id: Optional[int] = Field(default=None, primary_key=True)
    mandant_id: int
    wochentag: int = Field(ge=1, le=7)
    uhrzeit_von: time
    uhrzeit_bis: time
    pause_beginn: Optional[time] = None
    pause_ende: Optional[time] = None
    pause2_beginn: Optional[time] = None
    pause2_ende: Optional[time] = None
    anmerkung: Optional[str] = Field(default=None, max_length=80)


class FeiertagTable(SQLModel, table=True):
    __tablename__ = "feiertag"

    datum: date = Field(primary_key=True)
    feiertagsname: str = Field(max_length=80)
    hinweis: Optional[str] = Field(default=None, max_length=80)
    ist_halber_tag: bool = Field(default=False)
    ist_offiziell: bool = Field(default=True)


class UrlaubsantragTable(SQLModel, table=True):
    __tablename__ = "urlaubsantrag"

    id: Optional[int] = Field(default=None, primary_key=True)
    datum_von: date
    datum_bis: date
    urlaubstyp: str = Field(max_length=80)
    urlaubstage: float = Field(ge=0)
    genehmigt: bool = Field(default=False)


class KrankmeldungTable(SQLModel, table=True):
    __tablename__ = "krankmeldung"

    id: Optional[int] = Field(default=None, primary_key=True)
    krank_von: date
    krank_bis: date
    krankmeldungstage: int = Field(ge=0)


class BetriebsferienTable(SQLModel, table=True):
    __tablename__ = "betriebsferien"

    id: Optional[int] = Field(default=None, primary_key=True)
    mandant_id: int
    datum_von: date
    datum_bis: date
    betriebsferienname: str = Field(max_length=80)
    anmerkung: Optional[str] = Field(default=None, max_length=80)


class SchulferienTable(SQLModel, table=True):
    __tablename__ = "schulferien"

    id: Optional[int] = Field(default=None, primary_key=True)
    datum_von: date
    datum_bis: date
    schulferienname: str = Field(max_length=80)
    anmerkung: Optional[str] = Field(default=None, max_length=80)
