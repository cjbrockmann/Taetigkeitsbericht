from __future__ import annotations

from datetime import date

import pytest

from Core.Application.zeiteintrag_anwendung import ZeiteintragAnwendung
from Core.Domain.services.zeiteintrag_service import ZeiteintragService
from test.support.factories import stundenplan_montag
from test.support.fakes import InMemoryZeiteintragRepository


def test_erfasse_aus_stundenplan_falscher_wochentag():
    repo = InMemoryZeiteintragRepository()
    app = ZeiteintragAnwendung(ZeiteintragService(repo))
    # 2025-03-10 ist Montag (1); Stundenplan mit wochentag=2 passt nicht
    plan = stundenplan_montag()
    plan = plan.model_copy(update={"wochentag": 2})
    with pytest.raises(ValueError, match="Wochentag"):
        app.erfasse_aus_stundenplan(date(2025, 3, 10), plan)
