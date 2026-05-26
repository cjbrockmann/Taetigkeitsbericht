from __future__ import annotations

from datetime import time
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class ArbeitszeitBasis(BaseModel):
    uhrzeit_von: time = Field(description="Startzeit")
    uhrzeit_bis: time = Field(description="Endzeit")
    pause_beginn: Optional[time] = Field(default=None, description="Start der Unterbrechung")
    pause_ende: Optional[time] = Field(default=None, description="Ende der Unterbrechung")
    pause2_beginn: Optional[time] = Field(default=None, description="Start der zweiten Unterbrechung")
    pause2_ende: Optional[time] = Field(default=None, description="Ende der zweiten Unterbrechung")
    anmerkung: Optional[str] = Field(default=None, max_length=80)

    @staticmethod
    def _zeit_im_arbeitszeitfenster(zeit: time, uhrzeit_von: time, uhrzeit_bis: time) -> bool:
        return uhrzeit_von <= zeit <= uhrzeit_bis

    def _pruefe_pause_einzelzeit(
        self,
        zeit: time | None,
        feldname: str,
        uhrzeit_von: time,
        uhrzeit_bis: time,
    ) -> None:
        if zeit is None:
            return
        if not self._zeit_im_arbeitszeitfenster(zeit, uhrzeit_von, uhrzeit_bis):
            raise ValueError(
                f"{feldname} muss zwischen uhrzeit_von und uhrzeit_bis liegen."
            )

    @staticmethod
    def _pausen_intervalle_ueberlappen(
        beginn_a: time,
        ende_a: time,
        beginn_b: time,
        ende_b: time,
    ) -> bool:
        return beginn_a < ende_b and beginn_b < ende_a

    def _hat_gesetzte_pause(self) -> bool:
        return any(
            (
                self.pause_beginn,
                self.pause_ende,
                self.pause2_beginn,
                self.pause2_ende,
            )
        )

    @model_validator(mode="after")
    def pruefe_zeitraeume(self) -> ArbeitszeitBasis:
        if self.uhrzeit_von is not None and self.uhrzeit_bis is not None:
            if self.uhrzeit_von > self.uhrzeit_bis:
                raise ValueError(
                    "uhrzeit_von darf nicht nach uhrzeit_bis liegen."
                )

            if self.uhrzeit_von == self.uhrzeit_bis and self._hat_gesetzte_pause():
                raise ValueError(
                    "Bei gleicher Arbeitszeit (uhrzeit_von = uhrzeit_bis) "
                    "dürfen keine Pausen gesetzt sein."
                )

            for feldname, zeit in (
                ("pause_beginn", self.pause_beginn),
                ("pause_ende", self.pause_ende),
                ("pause2_beginn", self.pause2_beginn),
                ("pause2_ende", self.pause2_ende),
            ):
                self._pruefe_pause_einzelzeit(
                    zeit, feldname, self.uhrzeit_von, self.uhrzeit_bis
                )

        if (self.pause_beginn is None) ^ (self.pause_ende is None):
            raise ValueError("pause_beginn und pause_ende müssen gemeinsam gesetzt sein.")

        if self.pause_beginn and self.pause_ende:
            if self.pause_beginn >= self.pause_ende:
                raise ValueError("pause_beginn muss vor pause_ende liegen.")

        if (self.pause2_beginn is None) ^ (self.pause2_ende is None):
            raise ValueError("pause2_beginn und pause2_ende müssen gemeinsam gesetzt sein.")

        if self.pause2_beginn and self.pause2_ende:
            if self.pause2_beginn >= self.pause2_ende:
                raise ValueError("pause2_beginn muss vor pause2_ende liegen.")

        if (
            self.pause_beginn
            and self.pause_ende
            and self.pause2_beginn
            and self.pause2_ende
            and self._pausen_intervalle_ueberlappen(
                self.pause_beginn,
                self.pause_ende,
                self.pause2_beginn,
                self.pause2_ende,
            )
        ):
            raise ValueError("Pause 1 und Pause 2 dürfen sich nicht überlappen.")

        return self
