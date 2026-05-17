from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import urllib.request
from typing import Any, Optional
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

    def aktualisiere_feiertag(self, eintrag: Feiertag) -> bool:
        if not self._repository.get_by_datum(eintrag.datum):
            raise ValueError("Kein Feiertag fuer dieses Datum vorhanden.")
        return self._repository.update(eintrag)

    def hole_feiertag(self, datum: date) -> list[Feiertag]:
        return self._repository.get_by_datum(datum)

    def liste_feiertage(self, jahr: Optional[int] = None) -> list[Feiertag]:
        return self._repository.list_all(jahr=jahr)

    def loesche_feiertag(self, datum: date) -> bool:
        return self._repository.delete_by_datum(datum)

    @staticmethod
    def _src_verzeichnis() -> Path:
        return Path(__file__).resolve().parents[3]

    @classmethod
    def _feiertage_api_config(cls) -> dict[str, Any]:
        config_path = cls._src_verzeichnis() / "external_api.toml"
        with config_path.open("rb") as config_file:
            config = tomllib.load(config_file)
        api_config = config.get("feiertage_api", {})
        if not isinstance(api_config, dict):
            raise ValueError("feiertage_api in src/external_api.toml ist ungueltig.")
        return api_config

    def lade_feiertage_aus_api(self, jahr: int) -> list[Feiertag]:
        if jahr < 1900:
            raise ValueError("jahr muss >= 1900 sein.")

        api_config = self._feiertage_api_config()
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
            hinweis = self._hinweis_aus_api_eintrag(eintrag)
            feiertage.append(
                Feiertag(
                    datum=datum,
                    feiertagsname=feiertagsname,
                    hinweis=hinweis,
                    ist_halber_tag=False,
                    ist_offiziell=True,
                )
            )

        return feiertage

    def lade_zusaetzliche_feiertage_fuer_import(self, jahr: int) -> list[Feiertag]:
        """Zusaetzliche Tage aus JSON (nur fuer Internet-Import, z. B. Heiligabend/Silvester)."""
        api_config = self._feiertage_api_config()
        dateiname = str(api_config.get("zusatz_import_datei", "")).strip()
        if not dateiname:
            return []

        json_pfad = self._src_verzeichnis() / dateiname
        if not json_pfad.is_file():
            return []

        with json_pfad.open(encoding="utf-8") as datei:
            payload = json.load(datei)

        roh_liste = payload.get("zusaetzliche_tage", [])
        if not isinstance(roh_liste, list):
            raise ValueError(f"{dateiname}: 'zusaetzliche_tage' muss eine Liste sein.")

        feiertage: list[Feiertag] = []
        for idx, roh in enumerate(roh_liste):
            if not isinstance(roh, dict):
                continue
            try:
                monat = int(roh["monat"])
                tag = int(roh["tag"])
                datum = date(jahr, monat, tag)
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(
                    f"{dateiname}: Eintrag {idx} braucht gueltige 'monat' und 'tag'."
                ) from exc

            name = str(roh.get("feiertagsname", "")).strip()
            if not name:
                raise ValueError(f"{dateiname}: Eintrag {idx} ohne 'feiertagsname'.")

            feiertage.append(
                Feiertag(
                    datum=datum,
                    feiertagsname=name[:80],
                    hinweis=self._optional_hinweis(roh.get("hinweis")),
                    ist_halber_tag=bool(roh.get("ist_halber_tag", False)),
                    ist_offiziell=bool(roh.get("ist_offiziell", False)),
                )
            )
        return feiertage

    def importiere_feiertage_aus_api(self, jahr: int) -> tuple[int, int]:
        geladene_feiertage = self.lade_feiertage_aus_api(jahr=jahr)
        zusaetzliche = self.lade_zusaetzliche_feiertage_fuer_import(jahr=jahr)
        nach_datum: dict[date, Feiertag] = {f.datum: f for f in geladene_feiertage}
        for feiertag in zusaetzliche:
            nach_datum[feiertag.datum] = feiertag

        neu = 0
        aktualisiert = 0
        for feiertag in sorted(nach_datum.values(), key=lambda f: f.datum):
            if self._repository.get_by_datum(feiertag.datum):
                if self._repository.update(feiertag):
                    aktualisiert += 1
                continue
            self._repository.add(feiertag)
            neu += 1
        return neu, aktualisiert

    @staticmethod
    def _hinweis_aus_api_eintrag(eintrag: dict[str, Any]) -> str | None:
        hinweis_roh = eintrag.get("hinweis", "")
        hinweis_text = str(hinweis_roh).strip() if hinweis_roh is not None else ""
        if len(hinweis_text) > 80:
            hinweis_text = hinweis_text[:80]
        return hinweis_text if hinweis_text else None

    @staticmethod
    def _optional_hinweis(roh: Any) -> str | None:
        if roh is None:
            return None
        text = str(roh).strip()
        if not text:
            return None
        return text[:80]
