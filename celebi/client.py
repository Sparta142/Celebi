from __future__ import annotations as _annotations

import logging
import os

import aiopoke
import discord
from discord import app_commands
from discord.app_commands import CommandInvokeError, TransformerError
from discord.ext.commands import Bot
from pydantic import ValidationError

from celebi import utils
from celebi.astonish.client import AstonishClient
from celebi.discord.transformers import (
    CharacterNotFoundError,
    PokemonNotFoundError,
)
from celebi.ext.astonish import RestrictedCharacterError, UserMismatchError
from celebi.presentation import Presentation

logger = logging.getLogger(__name__)

GUILD = discord.Object(os.environ['CELEBI_GUILD_ID'])
ASTONISH_USERNAME = os.environ['ASTONISH_USERNAME']
ASTONISH_PASSWORD = os.environ['ASTONISH_PASSWORD']


class CelebiClient(Bot):
    def __init__(self) -> None:
        super().__init__([], intents=discord.Intents.default())

        self.activity = discord.Game('Pokémon')
        self.allowed_mentions = discord.AllowedMentions.none()

        self._presentation: Presentation | None = None

        # Initialized in .setup_hook()
        self.poke_client: aiopoke.AiopokeClient
        self.astonish_client: AstonishClient

    @property
    def presentation(self) -> Presentation:
        if self._presentation is None:
            guild = self.get_guild(GUILD.id)
            assert guild is not None
            self._presentation = Presentation(guild, self.astonish_client)

        return self._presentation

    async def setup_hook(self) -> None:
        self.poke_client = aiopoke.AiopokeClient()
        self.astonish_client = AstonishClient(
            ASTONISH_USERNAME,
            ASTONISH_PASSWORD,
        )
        await self.astonish_client.__aenter__()

        # Load bot extensions
        await self.load_extension('celebi.ext.astonish')
        await self.load_extension('celebi.ext.owner')
        await self.load_extension('celebi.ext.pokemon')

        # Sync app commands
        self.tree.copy_global_to(guild=GUILD)
        await self.tree.sync(guild=GUILD)

    async def close(self) -> None:
        if self._closed:
            return

        await self.astonish_client.close()
        await self.poke_client.close()
        return await super().close()

    async def on_ready(self) -> None:
        logger.info('Ready! Logged in as @%s', self.user)

    async def reload_all_extensions(self, *, sync: bool = False) -> None:
        """
        Reload all loaded extensions,
        then re-sync the command tree if requested.
        """

        # Create and iterate a list because otherwise we would mutate
        # a container while iterating over it (and raise an exception).
        for name in list(self.extensions):
            await self.reload_extension(name)

        if sync:
            self.tree.copy_global_to(guild=GUILD)
            await self.tree.sync(guild=GUILD)


CelebiInteraction = discord.Interaction[CelebiClient]
client = CelebiClient()


# Global handler for errors that can be handled cleanly somehow
@client.tree.error
async def on_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError,
) -> None:
    assert isinstance(interaction.client, CelebiClient)

    match error:
        case TransformerError(__cause__=PokemonNotFoundError()):
            logger.warning('Failed to query Pokemon matching %r', error.value)
            content = "I couldn't find a Pokémon matching your search."

        case TransformerError(__cause__=CharacterNotFoundError()):
            logger.warning(
                'Failed to query ASTONISH character matching %r',
                error.value,
            )
            content = "I couldn't find a character matching your search."

        case CommandInvokeError(original=RestrictedCharacterError()):
            content = "That character's profile is unavailable."

        case CommandInvokeError(original=UserMismatchError()):
            content = 'That information can only be viewed by their owner.'

        case ValidationError() as e:
            logger.error('Failed to parse data model:', exc_info=e)
            content = (
                'There was a problem with the data you requested.\n'
                'The data you requested may be corrupted somehow, '
                'or (more likely) the bot needs an update to address this.'
            )

        case _:
            logger.error(
                'Unknown failure when executing command',
                exc_info=error,
            )
            content = (
                'Something went wrong while running your command. '
                'Try again in a little while.\n'
                'If this keeps happening, please contact a staff member '
                'for help.'
            )

    # We made it here so we must have a message to send
    await utils.respond(interaction, content, ephemeral=True)
