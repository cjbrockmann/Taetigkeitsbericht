from __future__ import annotations

import pytest

from Core.Application.zeiteintrag_dto_anwendung import ZeiteintragAnwendungDTO
from test.support.fakes import dto_anwendung


@pytest.fixture
def dto_app() -> ZeiteintragAnwendungDTO:
    return dto_anwendung()
