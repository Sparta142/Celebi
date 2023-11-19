from typing import Any

from discord import Client
from discord.abc import Snowflake
from discord.app_commands import CommandTree
from discord.flags import Intents


class SingleGuildClient(Client):
    """
    A :class:`discord.Client` that only supports
    a single :class:`discord.Guild`.
    """

    def __init__(
        self,
        *,
        guild: Snowflake,
        intents: Intents,
        **options: Any,
    ) -> None:
        super().__init__(intents=intents, **options)

        self.guild = guild
        self.tree = CommandTree(self, fallback_to_global=False)

    async def setup_hook(self) -> None:
        self.tree.copy_global_to(guild=self.guild)
        await self.tree.sync(guild=self.guild)
