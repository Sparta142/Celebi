from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext.commands import Bot, GroupCog

from celebi.client import CelebiClient, CelebiInteraction
from celebi.discord.views import ConfirmationView

logger = logging.getLogger(__name__)


async def _is_owner(interaction: discord.Interaction[Bot], /) -> bool:
    return await interaction.client.is_owner(interaction.user)


@app_commands.check(_is_owner)
@app_commands.default_permissions()  # Hide this group from non-admins
class OwnerCog(
    GroupCog,
    name='owner',
    description=(
        'Commands that only owners of this Discord application may use, '
        'regardless of integration overrides.'
    ),
):
    @app_commands.command()
    async def reload(
        self,
        interaction: CelebiInteraction,
        sync: bool = False,
    ) -> None:
        """
        Reload all bot extensions.

        :param sync: Whether to sync the command tree after reloading.
        """
        username = interaction.user.name

        logger.info(
            'User %r is reloading the bot (sync: %s)...', username, sync
        )

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

    # Only allow termination by command if there's a reasonable chance
    # the bot can self-recover from it. Generally, only in Docker
    # (assuming a proper restart policy for the container is configured).
    if discord.utils.is_docker():

        @app_commands.command()
        async def terminate(self, interaction: CelebiInteraction) -> None:
            """Terminate the bot process."""

            continuation = await ConfirmationView.display(
                interaction,
                'Are you **absolutely sure** you want the bot to terminate?',
                timeout=3,
            )

            if not continuation:
                return

            logger.critical(
                'User %r has terminated this process',
                interaction.user.name,
            )
            await continuation.response.send_message('Goodbye!', ephemeral=True)
            await interaction.client.close()

        logger.info(
            "Running in Docker; '/%s' is available",
            terminate.qualified_name,
        )

    else:
        logger.info('Not running in Docker; terminate sub-command unavailable')


async def setup(bot: CelebiClient) -> None:
    await bot.add_cog(OwnerCog())
