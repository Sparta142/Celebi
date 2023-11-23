import logging

import discord
from discord import app_commands

from celebi.client import CelebiClient, client
from celebi.discord.transformers import PokemonTransformer

logger = logging.getLogger(__name__)


@client.tree.command()
@app_commands.guild_only()
@app_commands.rename(name_or_id='pokemon')
async def pokemon(
    interaction: discord.Interaction[CelebiClient],
    name_or_id: app_commands.Transform[str | int, PokemonTransformer],
    shiny: bool = False,
):
    """
    Shows information about a Pokémon from PokéAPI.

    :param name_or_id: The name or numeric ID of the Pokémon to search for.
    :param shiny: Whether to show details about the shiny variant of the Pokémon.
    """
    client = interaction.client

    try:
        pkmn = await client.poke_client.get_pokemon(name_or_id)
    except ValueError:
        logger.warning('User tried to get an unknown Pokemon: %r', name_or_id)
        await interaction.response.send_message(
            f"I couldn't find a Pokémon matching:\n>>> {name_or_id}",
            ephemeral=True,
        )
        return

    embed = await client.presentation.embed_pokemon(pkmn, shiny)
    await interaction.response.send_message(embed=embed)
