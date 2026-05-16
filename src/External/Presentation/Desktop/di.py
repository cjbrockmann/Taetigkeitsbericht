from __future__ import annotations

from injector import Module, provider, singleton

from App.app_config import AppConfig
from Core.Application.betriebsferien_anwendung import BetriebsferienAnwendung
from Core.Application.feiertag_anwendung import FeiertagAnwendung
from Core.Application.krankmeldung_anwendung import KrankmeldungAnwendung
from Core.Application.schulferien_anwendung import SchulferienAnwendung
from Core.Application.stundenplan_anwendung import StundenplanAnwendung
from Core.Application.urlaubsantrag_anwendung import UrlaubsantragAnwendung
from Core.Application.zeiteintrag_anwendung import ZeiteintragAnwendung
from External.Presentation.Desktop.feiertag_registry import FeiertagRegistry
from External.Presentation.Desktop.feiertag_view import FeiertagView
from External.Presentation.Desktop.feiertag_view_model import FeiertagViewModel
from External.Presentation.Desktop.stundenplan_registry import StundenplanRegistry
from External.Presentation.Desktop.stundenplan_view import StundenplanView
from External.Presentation.Desktop.stundenplan_view_model import StundenplanViewModel
from External.Presentation.Desktop.betriebsferien_view import BetriebsferienView
from External.Presentation.Desktop.betriebsferien_view_model import BetriebsferienViewModel
from External.Presentation.Desktop.krankmeldung_view import KrankmeldungView
from External.Presentation.Desktop.krankmeldung_view_model import KrankmeldungViewModel
from External.Presentation.Desktop.schulferien_view import SchulferienView
from External.Presentation.Desktop.schulferien_view_model import SchulferienViewModel
from External.Presentation.Desktop.urlaubsantrag_view import UrlaubsantragView
from External.Presentation.Desktop.urlaubsantrag_view_model import UrlaubsantragViewModel
from External.Presentation.Desktop.zeiteintrag_view_model import ZeiteintragViewModel
from External.Presentation.Desktop.zeiteintrag_window import ZeiteintragWindow


class DesktopPresentationDIModule(Module):
    @singleton
    @provider
    def provide_feiertag_registry(self) -> FeiertagRegistry:
        return FeiertagRegistry()

    @singleton
    @provider
    def provide_stundenplan_registry(self) -> StundenplanRegistry:
        return StundenplanRegistry()

    @provider
    def provide_zeiteintrag_view_model(
        self,
        anwendung: ZeiteintragAnwendung,
        feiertag_anwendung: FeiertagAnwendung,
        feiertag_registry: FeiertagRegistry,
        stundenplan_anwendung: StundenplanAnwendung,
        stundenplan_registry: StundenplanRegistry,
        stundenplan_view_model: StundenplanViewModel,
    ) -> ZeiteintragViewModel:
        return ZeiteintragViewModel(
            anwendung,
            feiertag_anwendung,
            feiertag_registry,
            stundenplan_anwendung,
            stundenplan_registry,
            stundenplan_view_model,
        )

    @singleton
    @provider
    def provide_stundenplan_view_model(
        self,
        anwendung: StundenplanAnwendung,
        stundenplan_registry: StundenplanRegistry,
    ) -> StundenplanViewModel:
        return StundenplanViewModel(anwendung, stundenplan_registry)

    @provider
    def provide_feiertag_view_model(
        self,
        anwendung: FeiertagAnwendung,
        feiertag_registry: FeiertagRegistry,
    ) -> FeiertagViewModel:
        return FeiertagViewModel(anwendung, feiertag_registry)

    @provider
    def provide_urlaubsantrag_view_model(
        self, anwendung: UrlaubsantragAnwendung
    ) -> UrlaubsantragViewModel:
        return UrlaubsantragViewModel(anwendung)

    @provider
    def provide_krankmeldung_view_model(
        self, anwendung: KrankmeldungAnwendung
    ) -> KrankmeldungViewModel:
        return KrankmeldungViewModel(anwendung)

    @provider
    def provide_betriebsferien_view_model(
        self, anwendung: BetriebsferienAnwendung
    ) -> BetriebsferienViewModel:
        return BetriebsferienViewModel(anwendung)

    @provider
    def provide_schulferien_view_model(
        self, anwendung: SchulferienAnwendung
    ) -> SchulferienViewModel:
        return SchulferienViewModel(anwendung)

    @provider
    def provide_stundenplan_view(
        self,
        view_model: StundenplanViewModel,
        app_config: AppConfig,
    ) -> StundenplanView:
        return StundenplanView(
            view_model,
            ausgeblendete_spalten=app_config.stundenplan_ausgeblendete_spalten,
        )

    @provider
    def provide_feiertag_view(
        self, view_model: FeiertagViewModel
    ) -> FeiertagView:
        return FeiertagView(view_model)

    @provider
    def provide_urlaubsantrag_view(
        self, view_model: UrlaubsantragViewModel
    ) -> UrlaubsantragView:
        return UrlaubsantragView(view_model)

    @provider
    def provide_krankmeldung_view(
        self, view_model: KrankmeldungViewModel
    ) -> KrankmeldungView:
        return KrankmeldungView(view_model)

    @provider
    def provide_betriebsferien_view(
        self, view_model: BetriebsferienViewModel
    ) -> BetriebsferienView:
        return BetriebsferienView(view_model)

    @provider
    def provide_schulferien_view(
        self, view_model: SchulferienViewModel
    ) -> SchulferienView:
        return SchulferienView(view_model)

    @provider
    def provide_zeiteintrag_window(
        self,
        view_model: ZeiteintragViewModel,
        stundenplan_view: StundenplanView,
        feiertag_view: FeiertagView,
        urlaubsantrag_view: UrlaubsantragView,
        krankmeldung_view: KrankmeldungView,
        betriebsferien_view: BetriebsferienView,
        schulferien_view: SchulferienView,
        app_config: AppConfig,
    ) -> ZeiteintragWindow:
        return ZeiteintragWindow(
            view_model,
            stundenplan_view,
            feiertag_view,
            urlaubsantrag_view,
            krankmeldung_view,
            betriebsferien_view,
            schulferien_view,
            excel_export=app_config.zeiteintrag_excel_export,
            ausgeblendete_spalten=app_config.zeiteintrag_ausgeblendete_spalten,
        )
