from __future__ import annotations

import logging
import os

import aiopoke
import discord
from discord import app_commands
from discord.app_commands import CommandInvokeError, TransformerError
from discord.ext.commands import Bot
from pydantic import ValidationError
from ruamel.yaml import YAML

from celebi.astonish.client import AstonishClient
from celebi.astonish.models import RestrictedCharacterError, UserMismatchError
from celebi.config import Config
from celebi.discord.transformers import (
    CharacterNotFoundError,
    PokemonNotFoundError,
)
from celebi.presentation import Presentation

logger = logging.getLogger(__name__)

GUILD = discord.Object(os.environ['CELEBI_GUILD_ID'])
ASTONISH_USERNAME = os.environ['ASTONISH_USERNAME']
ASTONISH_PASSWORD = os.environ['ASTONISH_PASSWORD']


class CelebiClient(Bot):
    def __init__(self, config: Config) -> None:
        super().__init__('', intents=discord.Intents.default())

        self.activity = discord.Game('Pokémon')
        self.allowed_mentions = discord.AllowedMentions.none()

        self.config = config
        self._presentation: Presentation | None = None

        # Initialized in .setup_hook()
        self.poke_client: aiopoke.AiopokeClient
        self.astonish_client: AstonishClient

    @property
    def presentation(self) -> Presentation:
        if self._presentation is None:
            guild = self.get_guild(GUILD.id)
            assert guild is not None
            self._presentation = Presentation(self.config.presentation, guild)

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


# TODO: MOVE THIS
def get_config():
    yaml = YAML(typ='safe')

    with open('config.yaml', 'rt') as f:
        return Config.model_validate(yaml.load(f))


client = CelebiClient(get_config())


async def is_owner(interaction: CelebiInteraction) -> bool:
    return await interaction.client.is_owner(interaction.user)


@client.tree.command()
@app_commands.check(is_owner)
async def reload(interaction: CelebiInteraction, sync: bool = False) -> None:
    username = interaction.user.name

    logger.info('User %r is reloading the bot (sync: %s)...', username, sync)

    await interaction.response.defer(ephemeral=True, thinking=True)

    try:
        await interaction.client.reload_all_extensions(sync=sync)
    except BaseException as e:
        await interaction.followup.send(
            'Reload failed, more details may be available in the log.',
            ephemeral=True,
        )
        logger.exception('Reload (by %r) failed', username, exc_info=e)
    else:
        await interaction.followup.send('Done!', ephemeral=True)
        logger.info('Reload (by %r) successful', username)


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
                'Try again in a little while.'
            )

    # We made it here so we must have a message to send
    await interaction.response.send_message(content, ephemeral=True)
