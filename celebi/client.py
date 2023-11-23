import logging
import os

import aiopoke
import discord
from ruamel.yaml import YAML

from celebi.astonish.client import AstonishClient
from celebi.config import Config
from celebi.discord.client import SingleGuildClient
from celebi.presentation import Presentation

logger = logging.getLogger(__name__)

GUILD = discord.Object(os.environ['CELEBI_GUILD_ID'])
ASTONISH_USERNAME = os.environ['ASTONISH_USERNAME']
ASTONISH_PASSWORD = os.environ['ASTONISH_PASSWORD']


class CelebiClient(SingleGuildClient):
    def __init__(self, config: Config) -> None:
        super().__init__(guild=GUILD, intents=discord.Intents.default())

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
            self._presentation = Presentation(
                self.config.presentation,
                guild,
            )

        return self._presentation

    async def setup_hook(self) -> None:
        self.poke_client = aiopoke.AiopokeClient()
        self.astonish_client = AstonishClient(
            ASTONISH_USERNAME,
            ASTONISH_PASSWORD,
        )
        await self.astonish_client.__aenter__()

        return await super().setup_hook()

    async def close(self) -> None:
        if self._closed:
            return

        await self.astonish_client.close()
        await self.poke_client.close()
        return await super().close()

    async def on_ready(self):
        logger.info('Ready! Logged in as @%s', self.user)


CelebiInteraction = discord.Interaction[CelebiClient]


# TODO: MOVE THIS
def get_config():
    yaml = YAML(typ='safe')

    with open('config.yaml', 'rt') as f:
        return Config.model_validate(yaml.load(f))


client = CelebiClient(get_config())

# For the side effect of the modules registering their commands
import celebi.ext.astonish  # noqa: E402, F401
import celebi.ext.pokemon  # noqa: E402, F401
