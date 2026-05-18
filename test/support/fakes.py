from __future__ import annotations

from datetime import date
from typing import Optional
from uuid import UUID, uuid4

from Core.Application.zeiteintrag_dto_anwendung import ZeiteintragAnwendungDTO
from Core.Domain.models.models_worktime import (
    Betriebsferien,
    Feiertag,
    Krankmeldung,
    Schulferien,
    Stundenplan,
    Urlaubsantrag,
    Zeiteintrag,
)
from Core.Domain.services.betriebsferien_service import BetriebsferienService
from Core.Domain.services.feiertag_service import FeiertagService
from Core.Domain.services.krankmeldung_service import KrankmeldungService
from Core.Domain.services.schulferien_service import SchulferienService
from Core.Domain.services.stundenplan_service import StundenplanService
from Core.Domain.services.urlaubsantrag_service import UrlaubsantragService
from Core.Domain.services.zeiteintrag_service import ZeiteintragService


class InMemoryZeiteintragRepository:
    def __init__(self) -> None:
        self._by_id: dict[UUID, Zeiteintrag] = {}

    def save(self, eintrag: Zeiteintrag) -> Zeiteintrag:
        if eintrag.id is None:
            eintrag = eintrag.model_copy(update={"id": uuid4()})
        self._by_id[eintrag.id] = eintrag
        return eintrag

    def get_by_datum(self, datum: date) -> list[Zeiteintrag]:
        return sorted(
            (e for e in self._by_id.values() if e.datum == datum),
            key=lambda e: e.uhrzeit_von,
        )

    def list_all(
        self, jahr: Optional[int] = None, monat: Optional[int] = None
    ) -> list[Zeiteintrag]:
        result = list(self._by_id.values())
        if jahr is not None:
            result = [e for e in result if e.datum.year == jahr]
        if monat is not None:
            result = [e for e in result if e.datum.month == monat]
        return sorted(result, key=lambda e: (e.datum, e.uhrzeit_von))

    def delete_by_datum(self, datum: date) -> bool:
        ids = [eid for eid, e in self._by_id.items() if e.datum == datum]
        for eid in ids:
            del self._by_id[eid]
        return bool(ids)

    def delete_by_id(self, eintrag_id: UUID) -> bool:
        if eintrag_id not in self._by_id:
            return False
        del self._by_id[eintrag_id]
        return True


class _FeiertagListRepo:
    def __init__(self, items: list[Feiertag]) -> None:
        self._items = list(items)

    def get_by_datum(self, datum: date) -> list[Feiertag]:
        return [f for f in self._items if f.datum == datum]

    def add(self, eintrag: Feiertag) -> Feiertag:
        self._items.append(eintrag)
        return eintrag

    def list_all(self, jahr: Optional[int] = None) -> list[Feiertag]:
        if jahr is None:
            return list(self._items)
        return [f for f in self._items if f.datum.year == jahr]


class _UrlaubListRepo:
    def __init__(self, items: list[Urlaubsantrag]) -> None:
        self._items = list(items)

    def list_all(
        self, jahr: Optional[int] = None, genehmigt: Optional[bool] = None
    ) -> list[Urlaubsantrag]:
        result = list(self._items)
        if jahr is not None:
            result = [
                u for u in result if u.datum_von.year == jahr or u.datum_bis.year == jahr
            ]
        if genehmigt is not None:
            result = [u for u in result if u.genehmigt == genehmigt]
        return result


class _KrankListRepo:
    def __init__(self, items: list[Krankmeldung]) -> None:
        self._items = list(items)

    def list_all(self, jahr: Optional[int] = None) -> list[Krankmeldung]:
        if jahr is None:
            return list(self._items)
        return [
            k for k in self._items if k.krank_von.year == jahr or k.krank_bis.year == jahr
        ]


class _SchulferienListRepo:
    def __init__(self, items: list[Schulferien]) -> None:
        self._items = list(items)

    def list_all(self, jahr: Optional[int] = None) -> list[Schulferien]:
        if jahr is None:
            return list(self._items)
        return [
            s for s in self._items if s.datum_von.year == jahr or s.datum_bis.year == jahr
        ]


class _BetriebsferienListRepo:
    def __init__(self, items: list[Betriebsferien]) -> None:
        self._items = list(items)

    def list_all(self, jahr: Optional[int] = None) -> list[Betriebsferien]:
        if jahr is None:
            return list(self._items)
        return [
            b for b in self._items if b.datum_von.year == jahr or b.datum_bis.year == jahr
        ]


class _StundenplanListRepo:
    def __init__(self, eintraege: list[Stundenplan]) -> None:
        self._eintraege = list(eintraege)

    def list_all(self) -> list[Stundenplan]:
        return list(self._eintraege)


def dto_anwendung(
    *,
    zeiteintraege: list[Zeiteintrag] | None = None,
    feiertage: list[Feiertag] | None = None,
    urlaub: list[Urlaubsantrag] | None = None,
    krank: list[Krankmeldung] | None = None,
    schulferien: list[Schulferien] | None = None,
    betriebsferien: list[Betriebsferien] | None = None,
    stundenplan: list[Stundenplan] | None = None,
    vertrag_stunden: dict[int, str] | None = None,
) -> ZeiteintragAnwendungDTO:
    ze_repo = InMemoryZeiteintragRepository()
    if zeiteintraege:
        for e in zeiteintraege:
            ze_repo.save(e)

    feiertage = feiertage or []
    urlaub = urlaub or []
    krank = krank or []
    schulferien = schulferien or []
    betriebsferien = betriebsferien or []
    stundenplan = stundenplan or []

    app = ZeiteintragAnwendungDTO(
        ZeiteintragService(ze_repo),
        StundenplanService(_StundenplanListRepo(stundenplan)),
        FeiertagService(_FeiertagListRepo(feiertage)),
        UrlaubsantragService(_UrlaubListRepo(urlaub)),
        KrankmeldungService(_KrankListRepo(krank)),
        SchulferienService(_SchulferienListRepo(schulferien)),
        BetriebsferienService(_BetriebsferienListRepo(betriebsferien)),
    )
    app.set_vertrag_stunden_nach_wochentag(
        vertrag_stunden
        or {1: "08:00", 2: "08:00", 3: "08:00", 4: "08:00", 5: "08:00", 6: "00:00", 7: "00:00"}
    )
    app.set_kommentar_urlaubstage("U")
    app.set_kommentar_krankheitstage("K")
    app.set_kommentar_urlaub_krank_modus("kuerzel")
    app.set_kommentar_ueberstunden_frei("Überstunden frei")
    return app
