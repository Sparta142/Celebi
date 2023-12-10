from __future__ import annotations as _annotations

from typing import Generic, TypeVar

from discord.app_commands import ContextMenu
from discord.ext.commands import Bot, Cog

__all__ = ['BaseCog']

TClient = TypeVar('TClient', bound=Bot)


class BaseCog(Cog, Generic[TClient]):
    def __init__(self, bot: TClient) -> None:
        self.bot = bot
        self._context_menus: list[ContextMenu] = []

    # https://github.com/Rapptz/discord.py/issues/7823
    def add_context_menu(self, menu: ContextMenu, /) -> None:
        self.bot.tree.add_command(menu)
        self._context_menus.append(menu)

    async def cog_unload(self) -> None:
        for menu in reversed(self._context_menus):
            self.bot.tree.remove_command(menu.name, type=menu.type)

        self._context_menus.clear()
