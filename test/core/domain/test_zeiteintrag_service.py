from __future__ import annotations

from datetime import date, time

import pytest

from Core.Domain.models.models_worktime import Zeiteintrag
from Core.Domain.services.zeiteintrag_service import ZeiteintragService
from test.support.factories import zeiteintrag
from test.support.fakes import InMemoryZeiteintragRepository


def test_erfasse_zeiteintrag_speichert_neu():
    repo = InMemoryZeiteintragRepository()
    service = ZeiteintragService(repo)
    eintrag = zeiteintrag(datum=date(2025, 4, 1))
    gespeichert = service.erfasse_zeiteintrag(eintrag)
    assert gespeichert.id is not None
    assert len(service.hole_zeiteintrag(1, date(2025, 4, 1))) == 1


def test_ueberschneidung_am_selben_tag_wirft_fehler():
    repo = InMemoryZeiteintragRepository()
    service = ZeiteintragService(repo)
    service.erfasse_zeiteintrag(
        Zeiteintrag(
            mandant_id=1,
            datum=date(2025, 4, 1),
            uhrzeit_von=time(8, 0),
            uhrzeit_bis=time(12, 0),
        )
    )
    with pytest.raises(ValueError, match="ueberschneidet"):
        service.erfasse_zeiteintrag(
            Zeiteintrag(
                mandant_id=1,
                datum=date(2025, 4, 1),
                uhrzeit_von=time(10, 0),
                uhrzeit_bis=time(14, 0),
            )
        )
