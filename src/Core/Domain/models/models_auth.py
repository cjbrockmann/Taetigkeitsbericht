from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class User(BaseModel):
    user_id: int = Field(ge=1, description="Primärschlüssel")
    username: str = Field(min_length=3, max_length=50, description="Eindeutiger Benutzername")
    email: str = Field(max_length=120, description="E-Mail-Adresse")
    password_hash: str = Field(min_length=20, max_length=255, description="Gehashter Passwortwert")
    is_active: bool = Field(default=True, description="Kennzeichnet einen aktiven Benutzer")


class Login(BaseModel):
    user_id: int = Field(ge=1, description="Referenz auf den Benutzer")
    timestamp: datetime = Field(description="Zeitpunkt des Login-Versuchs")
    logintrycounter: int = Field(ge=0, description="Anzahl der Login-Versuche")
    success: bool = Field(description="Kennzeichnet erfolgreichen Login")
    token: Optional[str] = Field(default=None, max_length=250, description="Anmeldetoken")

