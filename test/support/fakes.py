from __future__ import annotations

from datetime import date
from typing import Optional
from uuid import UUID, uuid4

from App.app_config import _hh_mm_zu_dezimalstunden
from Core.Application.guthaben_stunden_anwendung import GuthabenStundenAnwendung
from Core.Application.sollstunden_vertrag_anwendung import SollstundenVertragAnwendung
from Core.Application.zeiteintrag_dto_anwendung import ZeiteintragAnwendungDTO
from Core.Domain.models.models_worktime import (
    Betriebsferien,
    Feiertag,
    Krankmeldung,
    Schulferien,
    GuthabenStunden,
    SollstundenVertrag,
    Stundenplan,
    Urlaubsantrag,
    Zeiteintrag,
)
from Core.Domain.services.betriebsferien_service import BetriebsferienService
from Core.Domain.services.guthaben_stunden_service import GuthabenStundenService
from Core.Domain.services.sollstunden_vertrag_service import SollstundenVertragService
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
        if eintrag.mandant_id is None:
            raise ValueError("mandant_id ist erforderlich.")
        if eintrag.id is None:
            eintrag = eintrag.model_copy(update={"id": uuid4()})
        self._by_id[eintrag.id] = eintrag
        return eintrag

    def get_by_datum(self, mandant_id: int, datum: date) -> list[Zeiteintrag]:
        return sorted(
            (
                e
                for e in self._by_id.values()
                if e.mandant_id == mandant_id and e.datum == datum
            ),
            key=lambda e: e.uhrzeit_von,
        )

    def list_all(
        self,
        mandant_id: int,
        jahr: Optional[int] = None,
        monat: Optional[int] = None,
    ) -> list[Zeiteintrag]:
        result = [e for e in self._by_id.values() if e.mandant_id == mandant_id]
        if jahr is not None:
            result = [e for e in result if e.datum.year == jahr]
        if monat is not None:
            result = [e for e in result if e.datum.month == monat]
        return sorted(result, key=lambda e: (e.datum, e.uhrzeit_von))

    def delete_by_datum(self, mandant_id: int, datum: date) -> bool:
        ids = [
            eid
            for eid, e in self._by_id.items()
            if e.mandant_id == mandant_id and e.datum == datum
        ]
        for eid in ids:
            del self._by_id[eid]
        return bool(ids)

    def delete_by_id(self, mandant_id: int, eintrag_id: UUID) -> bool:
        eintrag = self._by_id.get(eintrag_id)
        if eintrag is None or eintrag.mandant_id != mandant_id:
            return False
        del self._by_id[eintrag_id]
        return True


class InMemoryStundenplanRepository:
    def __init__(self, eintraege: list[Stundenplan] | None = None) -> None:
        self._eintraege: list[Stundenplan] = list(eintraege or [])
        self._naechste_id = max((e.id or 0 for e in self._eintraege), default=0) + 1

    def save(self, eintrag: Stundenplan) -> Stundenplan:
        if eintrag.mandant_id is None:
            raise ValueError("mandant_id ist erforderlich.")
        if eintrag.id is not None:
            for idx, vorhanden in enumerate(self._eintraege):
                if vorhanden.id == eintrag.id:
                    self._eintraege[idx] = eintrag
                    return eintrag
        neu = eintrag.model_copy(update={"id": self._naechste_id})
        self._naechste_id += 1
        self._eintraege.append(neu)
        return neu

    def get_by_wochentag(self, mandant_id: int, wochentag: int) -> list[Stundenplan]:
        return sorted(
            (
                e
                for e in self._eintraege
                if e.mandant_id == mandant_id and e.wochentag == wochentag
            ),
            key=lambda e: e.uhrzeit_von,
        )

    def list_all(self, mandant_id: int) -> list[Stundenplan]:
        return sorted(
            (e for e in self._eintraege if e.mandant_id == mandant_id),
            key=lambda e: (e.wochentag, e.uhrzeit_von),
        )

    def delete_by_wochentag(self, mandant_id: int, wochentag: int) -> bool:
        vorher = len(self._eintraege)
        self._eintraege = [
            e
            for e in self._eintraege
            if not (e.mandant_id == mandant_id and e.wochentag == wochentag)
        ]
        return len(self._eintraege) < vorher

    def delete_by_id(self, mandant_id: int, eintrag_id: int) -> bool:
        vorher = len(self._eintraege)
        self._eintraege = [
            e
            for e in self._eintraege
            if not (e.id == eintrag_id and e.mandant_id == mandant_id)
        ]
        return len(self._eintraege) < vorher


class InMemoryBetriebsferienRepository:
    def __init__(self, items: list[Betriebsferien] | None = None) -> None:
        self._items: list[Betriebsferien] = list(items or [])
        self._naechste_id = max((e.id or 0 for e in self._items), default=0) + 1

    def save(self, eintrag: Betriebsferien) -> Betriebsferien:
        if eintrag.mandant_id is None:
            raise ValueError("mandant_id ist erforderlich.")
        if eintrag.id is not None:
            for idx, vorhanden in enumerate(self._items):
                if vorhanden.id == eintrag.id:
                    self._items[idx] = eintrag
                    return eintrag
        neu = eintrag.model_copy(update={"id": self._naechste_id})
        self._naechste_id += 1
        self._items.append(neu)
        return neu

    def get_by_id(self, mandant_id: int, eintrag_id: int) -> Optional[Betriebsferien]:
        for eintrag in self._items:
            if eintrag.id == eintrag_id and eintrag.mandant_id == mandant_id:
                return eintrag
        return None

    def list_all(self, mandant_id: int, jahr: Optional[int] = None) -> list[Betriebsferien]:
        result = [b for b in self._items if b.mandant_id == mandant_id]
        if jahr is None:
            return list(result)
        return [
            b
            for b in result
            if b.datum_von.year == jahr or b.datum_bis.year == jahr
        ]

    def delete_by_id(self, mandant_id: int, eintrag_id: int) -> bool:
        vorher = len(self._items)
        self._items = [
            b
            for b in self._items
            if not (b.id == eintrag_id and b.mandant_id == mandant_id)
        ]
        return len(self._items) < vorher


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


_WOCHENTAG_FELDER = (
    "Montag",
    "Dienstag",
    "Mittwoch",
    "Donnerstag",
    "Freitag",
    "Samstag",
    "Sonntag",
)


class InMemorySollstundenVertragRepository:
    def __init__(self) -> None:
        self._items: list[SollstundenVertrag] = []
        self._next_id = 1

    def save(self, vertrag: SollstundenVertrag) -> SollstundenVertrag:
        if vertrag.id is None:
            saved = vertrag.model_copy(update={"id": self._next_id})
            self._next_id += 1
            self._items.append(saved)
            return saved
        for index, vorhanden in enumerate(self._items):
            if vorhanden.id == vertrag.id:
                self._items[index] = vertrag
                return vertrag
        self._items.append(vertrag)
        return vertrag

    def get_by_id(self, mandant_id: int, vertrag_id: int) -> Optional[SollstundenVertrag]:
        for vertrag in self._items:
            if vertrag.id == vertrag_id and vertrag.mandant_id == mandant_id:
                return vertrag
        return None

    def list_all(self, mandant_id: int) -> list[SollstundenVertrag]:
        return [v for v in self._items if v.mandant_id == mandant_id]

    def get_gueltig_fuer_datum(
        self, mandant_id: int, datum: date
    ) -> Optional[SollstundenVertrag]:
        gueltig = [
            v
            for v in self._items
            if v.mandant_id == mandant_id
            and v.effective_date <= datum
            and (v.discontinued_date is None or v.discontinued_date > datum)
        ]
        if not gueltig:
            return None
        return max(gueltig, key=lambda v: v.effective_date)

    def delete_by_id(self, mandant_id: int, vertrag_id: int) -> bool:
        for index, vertrag in enumerate(self._items):
            if vertrag.id == vertrag_id and vertrag.mandant_id == mandant_id:
                del self._items[index]
                return True
        return False


class InMemoryGuthabenStundenRepository:
    def __init__(self) -> None:
        self._items: list[GuthabenStunden] = []
        self._next_id = 1

    def save(self, eintrag: GuthabenStunden) -> GuthabenStunden:
        if eintrag.id is None:
            saved = eintrag.model_copy(update={"id": self._next_id})
            self._next_id += 1
            self._items.append(saved)
            return saved
        for index, vorhanden in enumerate(self._items):
            if vorhanden.id == eintrag.id:
                self._items[index] = eintrag
                return eintrag
        self._items.append(eintrag)
        return eintrag

    def get_by_id(self, mandant_id: int, eintrag_id: int) -> Optional[GuthabenStunden]:
        for eintrag in self._items:
            if eintrag.id == eintrag_id and eintrag.mandant_id == mandant_id:
                return eintrag
        return None

    def get_by_mandant_und_datum(
        self, mandant_id: int, datum: date
    ) -> Optional[GuthabenStunden]:
        for eintrag in self._items:
            if eintrag.mandant_id == mandant_id and eintrag.datum == datum:
                return eintrag
        return None

    def list_all(
        self, mandant_id: int, jahr: Optional[int] = None
    ) -> list[GuthabenStunden]:
        items = [e for e in self._items if e.mandant_id == mandant_id]
        if jahr is None:
            return items
        return [e for e in items if e.datum.year == jahr]

    def delete_by_id(self, mandant_id: int, eintrag_id: int) -> bool:
        for index, eintrag in enumerate(self._items):
            if eintrag.id == eintrag_id and eintrag.mandant_id == mandant_id:
                del self._items[index]
                return True
        return False


def _sollstunden_vertrag_aus_mapping(
    mandant_id: int, stunden_nach_wochentag: dict[int, str]
) -> SollstundenVertrag:
    felder = {
        feld: _hh_mm_zu_dezimalstunden(stunden_nach_wochentag.get(index, "00:00"))
        for index, feld in enumerate(_WOCHENTAG_FELDER, start=1)
    }
    return SollstundenVertrag(
        mandant_id=mandant_id,
        effective_date=date(2000, 1, 1),
        **felder,
    )


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
    mandant_id: int = 1,
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

    sv_repo = InMemorySollstundenVertragRepository()
    sv_anwendung = SollstundenVertragAnwendung(SollstundenVertragService(sv_repo))
    sv_anwendung.erfasse(
        _sollstunden_vertrag_aus_mapping(
            mandant_id,
            vertrag_stunden
            or {
                1: "08:00",
                2: "08:00",
                3: "08:00",
                4: "08:00",
                5: "08:00",
                6: "00:00",
                7: "00:00",
            },
        )
    )

    gs_anwendung = GuthabenStundenAnwendung(
        GuthabenStundenService(InMemoryGuthabenStundenRepository())
    )

    app = ZeiteintragAnwendungDTO(
        ZeiteintragService(ze_repo),
        StundenplanService(InMemoryStundenplanRepository(stundenplan)),
        FeiertagService(_FeiertagListRepo(feiertage)),
        UrlaubsantragService(_UrlaubListRepo(urlaub)),
        KrankmeldungService(_KrankListRepo(krank)),
        SchulferienService(_SchulferienListRepo(schulferien)),
        BetriebsferienService(InMemoryBetriebsferienRepository(betriebsferien)),
        sv_anwendung,
        gs_anwendung,
    )
    app.set_kommentar_urlaubstage("U")
    app.set_kommentar_krankheitstage("K")
    app.set_kommentar_urlaub_krank_modus("kuerzel")
    app.set_kommentar_ueberstunden_frei("Überstunden frei")
    app.set_stundenplan_eintraege(stundenplan)
    return app
