from __future__ import annotations

from injector import Binder, Module, provider, singleton

from App.app_config import AppConfig
from Core.Application.betriebsferien_anwendung import BetriebsferienAnwendung
from Core.Application.feiertag_anwendung import FeiertagAnwendung
from Core.Application.krankmeldung_anwendung import KrankmeldungAnwendung
from Core.Application.schulferien_anwendung import SchulferienAnwendung
from Core.Application.stundenplan_anwendung import StundenplanAnwendung
from Core.Application.urlaubsantrag_anwendung import UrlaubsantragAnwendung
from Core.Application.zeiteintrag_anwendung import ZeiteintragAnwendung
from Core.Application.zeiteintrag_dto_anwendung import ZeiteintragAnwendungDTO
from Core.Domain.interfaces.auth_interface import IAuthService
from Core.Domain.interfaces.betriebsferien_repository_interface import IBetriebsferienRepository
from Core.Domain.interfaces.feiertag_repository_interface import IFeiertagRepository
from Core.Domain.interfaces.krankmeldung_repository_interface import IKrankmeldungRepository
from Core.Domain.interfaces.schulferien_repository_interface import ISchulferienRepository
from Core.Domain.interfaces.stundenplan_repository_interface import IStundenplanRepository
from Core.Domain.interfaces.urlaubsantrag_repository_interface import IUrlaubsantragRepository
from Core.Domain.interfaces.zeiteintrag_repository_interface import IZeiteintragRepository
from Core.Domain.services.auth_service import AuthService
from Core.Domain.services.betriebsferien_service import BetriebsferienService
from Core.Domain.services.feiertag_service import FeiertagService
from Core.Domain.services.krankmeldung_service import KrankmeldungService
from Core.Domain.services.schulferien_service import SchulferienService
from Core.Domain.services.stundenplan_service import StundenplanService
from Core.Domain.services.urlaubsantrag_service import UrlaubsantragService
from Core.Domain.services.zeiteintrag_service import ZeiteintragService


class ApplicationDIModule(Module):
    def configure(self, binder: Binder) -> None:
        binder.bind(IAuthService, to=AuthService)

    @provider
    def provide_zeiteintrag_service(
        self, repository: IZeiteintragRepository
    ) -> ZeiteintragService:
        return ZeiteintragService(repository)

    @provider
    def provide_stundenplan_service(
        self, repository: IStundenplanRepository
    ) -> StundenplanService:
        return StundenplanService(repository)

    @provider
    def provide_feiertag_service(self, repository: IFeiertagRepository) -> FeiertagService:
        return FeiertagService(repository)

    @provider
    def provide_urlaubsantrag_service(
        self, repository: IUrlaubsantragRepository
    ) -> UrlaubsantragService:
        return UrlaubsantragService(repository)

    @provider
    def provide_krankmeldung_service(
        self, repository: IKrankmeldungRepository
    ) -> KrankmeldungService:
        return KrankmeldungService(repository)

    @provider
    def provide_betriebsferien_service(
        self, repository: IBetriebsferienRepository
    ) -> BetriebsferienService:
        return BetriebsferienService(repository)

    @provider
    def provide_schulferien_service(
        self, repository: ISchulferienRepository
    ) -> SchulferienService:
        return SchulferienService(repository)

    @singleton
    @provider
    def provide_zeiteintrag_anwendung_dto(
        self,
        zeiteintrag_service: ZeiteintragService,
        stundenplan_service: StundenplanService,
        feiertag_service: FeiertagService,
        urlaubsantrag_service: UrlaubsantragService,
        krankmeldung_service: KrankmeldungService,
        schulferien_service: SchulferienService,
        betriebsferien_service: BetriebsferienService,
        app_config: AppConfig,
    ) -> ZeiteintragAnwendungDTO:
        anwendung = ZeiteintragAnwendungDTO(
            zeiteintrag_service,
            stundenplan_service,
            feiertag_service,
            urlaubsantrag_service,
            krankmeldung_service,
            schulferien_service,
            betriebsferien_service,
        )
        anwendung.set_vertrag_stunden_nach_wochentag(
            app_config.soll_nach_vertrag_nach_wochentag
        )
        anwendung.set_sollstunden_an_feiertagen(app_config.sollstunden_an_feiertagen)
        anwendung.set_kommentar_urlaubstage(app_config.kommentar_urlaubstage)
        anwendung.set_kommentar_krankheitstage(app_config.kommentar_krankheitstage)
        anwendung.set_kommentar_urlaub_krank_modus(app_config.kommentar_urlaub_krank_modus)
        anwendung.set_kommentar_ueberstunden_frei(app_config.kommentar_ueberstunden_frei)
        return anwendung

    @singleton
    @provider
    def provide_zeiteintrag_anwendung(
        self, dto: ZeiteintragAnwendungDTO
    ) -> ZeiteintragAnwendung:
        return dto

    @singleton
    @provider
    def provide_stundenplan_anwendung(
        self, service: StundenplanService
    ) -> StundenplanAnwendung:
        return StundenplanAnwendung(service)

    @singleton
    @provider
    def provide_feiertag_anwendung(self, service: FeiertagService) -> FeiertagAnwendung:
        return FeiertagAnwendung(service)

    @singleton
    @provider
    def provide_urlaubsantrag_anwendung(
        self, service: UrlaubsantragService
    ) -> UrlaubsantragAnwendung:
        return UrlaubsantragAnwendung(service)

    @singleton
    @provider
    def provide_krankmeldung_anwendung(
        self, service: KrankmeldungService
    ) -> KrankmeldungAnwendung:
        return KrankmeldungAnwendung(service)

    @singleton
    @provider
    def provide_betriebsferien_anwendung(
        self, service: BetriebsferienService
    ) -> BetriebsferienAnwendung:
        return BetriebsferienAnwendung(service)

    @singleton
    @provider
    def provide_schulferien_anwendung(
        self, service: SchulferienService
    ) -> SchulferienAnwendung:
        return SchulferienAnwendung(service)
