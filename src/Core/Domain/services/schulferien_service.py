from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Optional
import tomllib
import urllib.request

from ..interfaces.schulferien_repository_interface import ISchulferienRepository
from ..models.models_worktime import Schulferien

_CONFIG_RELATIV = Path(__file__).resolve().parents[3] / "external_api.toml"


def _iso_datum_aus_api(roh: str) -> date:
    text = roh.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    return datetime.fromisoformat(text).date()


class SchulferienService:
    def __init__(self, repository: ISchulferienRepository) -> None:
        self._repository = repository

    def erfasse_schulferien(self, eintrag: Schulferien) -> Schulferien:
        for vorhanden in self._repository.list_all(jahr=None):
            if eintrag.id is not None and vorhanden.id == eintrag.id:
                continue
            if (
                eintrag.datum_von <= vorhanden.datum_bis
                and vorhanden.datum_von <= eintrag.datum_bis
            ):
                von_s = vorhanden.datum_von.strftime("%d.%m.%Y")
                bis_s = vorhanden.datum_bis.strftime("%d.%m.%Y")
                raise ValueError(
                    f"Zeitraum ueberlappt mit vorhandenen Schulferien ({von_s} bis {bis_s})."
                )
        return self._repository.save(eintrag)

    def hole_schulferien(self, eintrag_id: int) -> Optional[Schulferien]:
        return self._repository.get_by_id(eintrag_id)

    def liste_schulferien(self, jahr: Optional[int] = None) -> list[Schulferien]:
        return self._repository.list_all(jahr=jahr)

    def loesche_schulferien(self, eintrag_id: int) -> bool:
        return self._repository.delete_by_id(eintrag_id)

    def lade_schulferien_aus_api(self, jahr: int) -> list[Schulferien]:
        if jahr < 1900:
            raise ValueError("jahr muss >= 1900 sein.")

        with _CONFIG_RELATIV.open("rb") as config_file:
            config = tomllib.load(config_file)
        api_config = config.get("schulferien_api", {})
        basis_url = str(api_config.get("url", "")).strip().rstrip("/")
        if not basis_url:
            raise ValueError("schulferien_api.url fehlt in src/external_api.toml.")
        bundesland_code = str(api_config.get("bundesland_code", "")).strip().upper()
        if not bundesland_code:
            raise ValueError("schulferien_api.bundesland_code fehlt in src/external_api.toml.")

        request_url = f"{basis_url}/v2/{jahr}/{bundesland_code}"

        request = urllib.request.Request(
            request_url,
            headers={"Accept": "application/json"},
            method="GET",
        )
        with urllib.request.urlopen(request, timeout=20) as response:  # noqa: S310
            payload = json.loads(response.read().decode("utf-8"))

        if not isinstance(payload, list):
            raise ValueError(
                "Unerwartetes Antwortformat der Schulferien-API (erwartet: JSON-Array)."
            )

        schulferien: list[Schulferien] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            start_roh = item.get("start")
            end_roh = item.get("end")
            name_cp = str(item.get("name_cp", "")).strip()
            if not start_roh or not end_roh or not name_cp:
                continue
            datum_von = _iso_datum_aus_api(str(start_roh))
            datum_bis = _iso_datum_aus_api(str(end_roh))
            state_code = str(item.get("stateCode", "")).strip()
            anmerkung: str | None = None
            if state_code:
                prefix = "Bundesland: "
                rest = self.get_bundesland_name(state_code)
                rest = rest[: max(0, 80 - len(prefix))]
                anmerkung = (prefix + rest) if rest else None
            schulferien.append(
                Schulferien(
                    id=None,
                    datum_von=datum_von,
                    datum_bis=datum_bis,
                    schulferienname=name_cp[:80],
                    anmerkung=anmerkung[:80] if anmerkung else None,
                )
            )
        return schulferien

    def importiere_schulferien_aus_api(self, jahr: int) -> tuple[int, int, int]:
        """Persistiert API-Ferien: gleicher Zeitraum wird aktualisiert, sonst neu; Konflikte zaehlen als uebersprungen."""
        api_eintraege = self.lade_schulferien_aus_api(jahr)
        known: list[Schulferien] = list(self._repository.list_all(jahr=None))
        neu = 0
        aktualisiert = 0
        uebersprungen = 0

        for api_e in api_eintraege:
            match = next(
                (
                    e
                    for e in known
                    if e.datum_von == api_e.datum_von and e.datum_bis == api_e.datum_bis
                ),
                None,
            )
            if match is not None:
                updated = self._repository.save(
                    Schulferien(
                        id=match.id,
                        datum_von=api_e.datum_von,
                        datum_bis=api_e.datum_bis,
                        schulferienname=api_e.schulferienname,
                        anmerkung=api_e.anmerkung,
                    )
                )
                idx = next(i for i, e in enumerate(known) if e.id == match.id)
                known[idx] = updated
                aktualisiert += 1
                continue
            try:
                saved = self.erfasse_schulferien(api_e)
                known.append(saved)
                neu += 1
            except ValueError:
                uebersprungen += 1
        return neu, aktualisiert, uebersprungen

    def get_bundesland_name(self, code: str) -> str | None:
        if not code:
            return None 
        bundeslaender = {
            "BW": "Baden-Württemberg",
            "BY": "Bayern",
            "BE": "Berlin",
            "BB": "Brandenburg",
            "HB": "Bremen",
            "HH": "Hamburg",
            "HE": "Hessen",
            "MV": "Mecklenburg-Vorpommern",
            "NI": "Niedersachsen",
            "NW": "Nordrhein-Westfalen",
            "RP": "Rheinland-Pfalz",
            "SL": "Saarland",
            "SN": "Sachsen",
            "ST": "Sachsen-Anhalt",
            "SH": "Schleswig-Holstein",
            "TH": "Thüringen"
            }
        if code.upper() not in bundeslaender:
            return code
        return bundeslaender[code.upper()]


