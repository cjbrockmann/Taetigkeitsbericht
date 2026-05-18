from __future__ import annotations

import sys
from pathlib import Path

from injector import Injector

# Erlaubt direkten Start dieser Datei ohne gesetztes PYTHONPATH.
SRC_ROOT = Path(__file__).resolve().parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from App.app_config import AppConfig, load_app_config
from Core.Application.di import ApplicationDIModule
from Core.Application.betriebsferien_anwendung import BetriebsferienAnwendung
from Core.Application.feiertag_anwendung import FeiertagAnwendung
from Core.Application.krankmeldung_anwendung import KrankmeldungAnwendung
from Core.Application.schulferien_anwendung import SchulferienAnwendung
from Core.Application.stundenplan_anwendung import StundenplanAnwendung
from Core.Application.urlaubsantrag_anwendung import UrlaubsantragAnwendung
from Core.Application.zeiteintrag_anwendung import ZeiteintragAnwendung
from External.Infrastructure.di import InfrastructureConfig, InfrastructureDIModule
from External.Presentation.Desktop.di import DesktopPresentationDIModule


def create_injector(
    database_url: str | None = None,
    app_config: AppConfig | None = None,
) -> Injector:
    if app_config is None:
        app_config = load_app_config()
    config = InfrastructureConfig(database_url=database_url)
    return Injector(
        [
            InfrastructureDIModule(),
            ApplicationDIModule(),
            DesktopPresentationDIModule(),
            lambda binder: binder.bind(InfrastructureConfig, to=config),
            lambda binder: binder.bind(AppConfig, to=app_config),
        ]
    )


def build_applications(injector_instance: Injector) -> tuple[
    ZeiteintragAnwendung,
    StundenplanAnwendung,
    FeiertagAnwendung,
    UrlaubsantragAnwendung,
    KrankmeldungAnwendung,
    BetriebsferienAnwendung,
    SchulferienAnwendung,
]:
    return (
        injector_instance.get(ZeiteintragAnwendung),
        injector_instance.get(StundenplanAnwendung),
        injector_instance.get(FeiertagAnwendung),
        injector_instance.get(UrlaubsantragAnwendung),
        injector_instance.get(KrankmeldungAnwendung),
        injector_instance.get(BetriebsferienAnwendung),
        injector_instance.get(SchulferienAnwendung),
    )
