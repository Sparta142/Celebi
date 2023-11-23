from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from discord import app_commands
from discord.ext.commands import Cog

from celebi.discord.transformers import TransformPokemon

if TYPE_CHECKING:
    from aiopoke import AiopokeClient

    from celebi.client import CelebiClient, CelebiInteraction
    from celebi.presentation import Presentation


logger = logging.getLogger(__name__)


class PokemonCog(Cog):
    def __init__(self, bot: CelebiClient) -> None:
        self.bot = bot

    @property
    def poke_client(self) -> AiopokeClient:
        return self.bot.poke_client

    @property
    def presentation(self) -> Presentation:
        return self.bot.presentation

    @app_commands.command()
    @app_commands.guild_only()
    @app_commands.rename(name_or_id='pokemon')
    async def pokemon(
        self,
        interaction: CelebiInteraction,
        name_or_id: TransformPokemon,
        shiny: bool = False,
    ) -> None:
        """
        Shows information about a Pokémon from PokéAPI.

        :param name_or_id: The name or numeric ID of the Pokémon to search for.
        :param shiny: Whether to show details about the shiny variant of the Pokémon.
        """
        try:
            pkmn = await self.poke_client.get_pokemon(name_or_id)
        except ValueError:
            logger.warning(
                'User tried to get an unknown Pokemon: %r', name_or_id
            )
            await interaction.response.send_message(
                f"I couldn't find a Pokémon matching:\n>>> {name_or_id}",
                ephemeral=True,
            )
            return

        embed = await self.presentation.embed_pokemon(pkmn, shiny=shiny)
        await interaction.response.send_message(embed=embed)


async def setup(bot: CelebiClient) -> None:
    await bot.add_cog(PokemonCog(bot))
