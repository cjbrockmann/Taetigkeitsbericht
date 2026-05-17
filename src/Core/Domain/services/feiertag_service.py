from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import urllib.request
from typing import Optional
import tomllib

from ..interfaces.feiertag_repository_interface import IFeiertagRepository
from ..models.models_worktime import Feiertag


class FeiertagService:
    def __init__(self, repository: IFeiertagRepository) -> None:
        self._repository = repository

    def erfasse_feiertag(self, eintrag: Feiertag) -> Feiertag:
        vorhandene_eintraege = self._repository.get_by_datum(eintrag.datum)
        if vorhandene_eintraege:
            raise ValueError("Pro Datum ist nur ein Feiertagseintrag erlaubt.")
        return self._repository.add(eintrag)

    def hole_feiertag(self, datum: date) -> list[Feiertag]:
        return self._repository.get_by_datum(datum)

    def liste_feiertage(self, jahr: Optional[int] = None) -> list[Feiertag]:
        return self._repository.list_all(jahr=jahr)

    def loesche_feiertag(self, datum: date) -> bool:
        return self._repository.delete_by_datum(datum)

    def lade_feiertage_aus_api(self, jahr: int) -> list[Feiertag]:
        if jahr < 1900:
            raise ValueError("jahr muss >= 1900 sein.")

        config_path = Path(__file__).resolve().parents[3] / "external_api.toml"
        with config_path.open("rb") as config_file:
            config = tomllib.load(config_file)
        api_config = config.get("feiertage_api", {})
        basis_url = str(api_config.get("url", "")).strip()
        if not basis_url:
            raise ValueError("feiertage_api.url fehlt in src/external_api.toml.")
        bundesland_code = str(api_config.get("bundesland_code", "")).strip().upper()
        if not bundesland_code:
            raise ValueError("feiertage_api.bundesland_code fehlt in src/external_api.toml.")

        trennzeichen = "&" if "?" in basis_url else "?"
        request_url = f"{basis_url}{trennzeichen}jahr={jahr}&nur_land={bundesland_code}"

        request = urllib.request.Request(
            request_url,
            headers={"Accept": "application/json"},
            method="GET",
        )
        with urllib.request.urlopen(request, timeout=20) as response:  # noqa: S310
            payload = json.loads(response.read().decode("utf-8"))

        feiertage: list[Feiertag] = []
        for feiertagsname, eintrag in payload.items():
            if not isinstance(eintrag, dict):
                continue
            datum_text = str(eintrag.get("datum", "")).strip()
            if not datum_text or not feiertagsname:
                continue
            try:
                datum = date.fromisoformat(datum_text)
            except ValueError:
                continue
            hinweis_roh = eintrag.get("hinweis", "")
            hinweis_text = str(hinweis_roh).strip() if hinweis_roh is not None else ""
            if len(hinweis_text) > 80:
                hinweis_text = hinweis_text[:80]
            hinweis: str | None = hinweis_text if hinweis_text else None
            feiertage.append(
                Feiertag(datum=datum, feiertagsname=feiertagsname, hinweis=hinweis)
            )

        return feiertage

    def importiere_feiertage_aus_api(self, jahr: int) -> tuple[int, int]:
        geladene_feiertage = self.lade_feiertage_aus_api(jahr=jahr)
        neu = 0
        aktualisiert = 0
        for feiertag in geladene_feiertage:
            if self._repository.get_by_datum(feiertag.datum):
                if self._repository.update(feiertag):
                    aktualisiert += 1
                continue
            self._repository.add(feiertag)
            neu += 1
        return neu, aktualisiert
