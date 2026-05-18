from __future__ import annotations

from datetime import date

import pytest

from Core.Domain.models.models_worktime import Feiertag
from Core.Domain.services.feiertag_service import FeiertagService
from test.support.fakes import _FeiertagListRepo


def test_erfasse_feiertag_doppeltes_datum():
    tag = date(2025, 5, 1)
    repo = _FeiertagListRepo([Feiertag(datum=tag, feiertagsname="Vorhanden")])
    service = FeiertagService(repo)
    with pytest.raises(ValueError, match="nur ein Feiertag"):
        service.erfasse_feiertag(Feiertag(datum=tag, feiertagsname="Neu"))
