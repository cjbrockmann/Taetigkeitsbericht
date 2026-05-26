from __future__ import annotations

from dataclasses import dataclass

from injector import Module, provider, singleton
from sqlmodel import Session

from Core.Domain.interfaces.betriebsferien_repository_interface import IBetriebsferienRepository
from Core.Domain.interfaces.feiertag_repository_interface import IFeiertagRepository
from Core.Domain.interfaces.guthaben_stunden_repository_interface import IGuthabenStundenRepository
from Core.Domain.interfaces.guthaben_urlaub_repository_interface import IGuthabenUrlaubRepository
from Core.Domain.interfaces.krankmeldung_repository_interface import IKrankmeldungRepository
from Core.Domain.interfaces.schulferien_repository_interface import ISchulferienRepository
from Core.Domain.interfaces.sollstunden_vertrag_repository_interface import ISollstundenVertragRepository
from Core.Domain.interfaces.stundenplan_repository_interface import IStundenplanRepository
from Core.Domain.interfaces.urlaubsantrag_repository_interface import IUrlaubsantragRepository
from Core.Domain.interfaces.zeiteintrag_repository_interface import IZeiteintragRepository
from External.Infrastructure.database import create_sqlite_engine, init_db
from External.Infrastructure.repositories.betriebsferien_sqlmodel_repository import SqlBetriebsferienRepository
from External.Infrastructure.repositories.feiertag_sqlmodel_repository import SqlFeiertagRepository
from External.Infrastructure.repositories.guthaben_stunden_sqlmodel_repository import SqlGuthabenStundenRepository
from External.Infrastructure.repositories.guthaben_urlaub_sqlmodel_repository import SqlGuthabenUrlaubRepository
from External.Infrastructure.repositories.krankmeldung_sqlmodel_repository import SqlKrankmeldungRepository
from External.Infrastructure.repositories.schulferien_sqlmodel_repository import SqlSchulferienRepository
from External.Infrastructure.repositories.sollstunden_vertrag_sqlmodel_repository import SqlSollstundenVertragRepository
from External.Infrastructure.repositories.stundenplan_sqlmodel_repository import SqlStundenplanRepository
from External.Infrastructure.repositories.urlaubsantrag_sqlmodel_repository import SqlUrlaubsantragRepository
from External.Infrastructure.repositories.zeiteintrag_sqlmodel_repository import SqlZeiteintragRepository


@dataclass(frozen=True)
class InfrastructureConfig:
    database_url: str | None = None


class InfrastructureDIModule(Module):
    @singleton
    @provider
    def provide_session(self, config: InfrastructureConfig) -> Session:
        engine = create_sqlite_engine(config.database_url)
        init_db(engine)
        return Session(engine)

    @provider
    def provide_feiertag_repository(self, session: Session) -> IFeiertagRepository:
        return SqlFeiertagRepository(session)

    @provider
    def provide_stundenplan_repository(self, session: Session) -> IStundenplanRepository:
        return SqlStundenplanRepository(session)

    @provider
    def provide_zeiteintrag_repository(self, session: Session) -> IZeiteintragRepository:
        return SqlZeiteintragRepository(session)

    @provider
    def provide_urlaubsantrag_repository(self, session: Session) -> IUrlaubsantragRepository:
        return SqlUrlaubsantragRepository(session)

    @provider
    def provide_krankmeldung_repository(self, session: Session) -> IKrankmeldungRepository:
        return SqlKrankmeldungRepository(session)

    @provider
    def provide_betriebsferien_repository(self, session: Session) -> IBetriebsferienRepository:
        return SqlBetriebsferienRepository(session)

    @provider
    def provide_schulferien_repository(self, session: Session) -> ISchulferienRepository:
        return SqlSchulferienRepository(session)

    @provider
    def provide_guthaben_urlaub_repository(
        self, session: Session
    ) -> IGuthabenUrlaubRepository:
        return SqlGuthabenUrlaubRepository(session)

    @provider
    def provide_guthaben_stunden_repository(
        self, session: Session
    ) -> IGuthabenStundenRepository:
        return SqlGuthabenStundenRepository(session)

    @provider
    def provide_sollstunden_vertrag_repository(
        self, session: Session
    ) -> ISollstundenVertragRepository:
        return SqlSollstundenVertragRepository(session)
