from __future__ import annotations as _annotations

import enum
from abc import ABC, abstractmethod
from collections.abc import Container
from typing import TYPE_CHECKING

from aiopoke import Pokemon

if TYPE_CHECKING:
    from celebi.astonish.client import AstonishClient
    from celebi.astonish.models import Character


class ItemBehavior(ABC):
    @abstractmethod
    async def use(self, client: AstonishClient, character: Character) -> None:
        raise NotImplementedError


class LureBehavior(ItemBehavior):
    def __init__(self, pokemon: Container[Pokemon]) -> None:
        self.pokemon = pokemon

    async def use(self, client: AstonishClient, character: Character) -> None:
        # TODO: Select 3 Pokemon, roll 70% chance of matching type for each slot
        # TODO: For each, roll 2% shiny chance
        # TODO: Present player with options and make changes accordingly
        raise NotImplementedError


# TODO: Does this need to be an enum?
class LureStage(enum.Enum):
    BABY = enum.auto()
    EVOLUTION_STAGE_1 = enum.auto()
    EVOLUTION_STAGE_2 = enum.auto()
    EVOLUTION_STAGE_3 = enum.auto()
    STARTER_STAGE_1 = enum.auto()
    STARTER_STAGE_2 = enum.auto()
    STARTER_STAGE_3 = enum.auto()
