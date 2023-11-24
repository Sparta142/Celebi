from __future__ import annotations

import logging
from typing import TYPE_CHECKING, ClassVar

import discord
from discord import app_commands, ui
from discord.ext.commands import Cog
from yarl import URL

from celebi.astonish.models import PersonalComputer, Pokemon
from celebi.discord.transformers import TransformCharacter, TransformPokemon
from celebi.discord.views import ConfirmationView, EmbedMenu
from celebi.utils import pokemon_name

if TYPE_CHECKING:
    from aiopoke import AiopokeClient

    from celebi.astonish.client import AstonishClient
    from celebi.client import CelebiClient, CelebiInteraction
    from celebi.presentation import Presentation


logger = logging.getLogger(__name__)


class AstonishCog(Cog):
    def __init__(self, bot: CelebiClient) -> None:
        self.bot = bot

        # https://github.com/Rapptz/discord.py/issues/7823
        self._link_profile_ctxm = app_commands.ContextMenu(
            name='Link Jcink profile',
            callback=self.link_profile,
        )
        self.bot.tree.add_command(self._link_profile_ctxm)

    @property
    def poke_client(self) -> AiopokeClient:
        return self.bot.poke_client

    @property
    def presentation(self) -> Presentation:
        return self.bot.presentation

    @property
    def astonish_client(self) -> AstonishClient:
        return self.bot.astonish_client

    async def cog_unload(self) -> None:
        # https://github.com/Rapptz/discord.py/issues/7823
        self.bot.tree.remove_command(
            self._link_profile_ctxm.name,
            type=self._link_profile_ctxm.type,
        )

    @app_commands.command()
    @app_commands.guild_only()
    async def team(
        self,
        interaction: CelebiInteraction,
        character: TransformCharacter,
    ) -> None:
        """
        Shows a character's Pokémon team (personal computer).

        :param character: The (partial) name or numeric ID of the character whose PC to show.
        """
        character.raise_if_restricted()

        # Get their team and ensure it has at least 1 Pokemon
        count = len(character.personal_computer)

        if not count:
            await interaction.response.send_message(
                f"{character.username} doesn't have any Pokémon in their PC.",
                ephemeral=True,
            )
            return

        # Defer in case the rest of the response takes a while to respond
        await interaction.response.defer()

        view = PokemonTeamView(
            interaction.user,
            character.personal_computer,
            self.presentation,
            self.poke_client,
        )
        embed = await view.create_embed(0)

        await interaction.followup.send(
            content=f'{character.markdown()} has {count} Pokémon on their team:',
            embed=embed,
            view=view,
        )

    @app_commands.command()
    @app_commands.guild_only()
    async def character(
        self,
        interaction: CelebiInteraction,
        character: TransformCharacter,
    ) -> None:
        """
        Shows a character's profile.

        :param character: The (partial) name or numeric ID of the character profile to show.
        """
        character.raise_if_restricted()

        # Generate an embed for the character
        try:
            embed = self.presentation.embed_character(character)
        except Exception:
            await interaction.response.send_message(
                "There was a problem displaying that character's profile.",
                ephemeral=True,
            )
            logger.error(
                'Failed to generate embed for character %r',
                character.username,
                exc_info=True,
            )
            return

        # Add the linked Discord user if available
        if character.extra.discord_id:
            embed.add_field(
                name='Played by',
                value=f'<@{character.extra.discord_id}>',
                inline=True,
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.guild_only()
    async def inventory(
        self,
        interaction: CelebiInteraction,
        character: TransformCharacter,
    ) -> None:
        """
        Shows your character's item inventory.

        :param character: The (partial) name or numeric ID of the character whose inventory to show.
        """
        character.raise_if_restricted()
        character.raise_if_user_mismatch(interaction.user)

        inventory = await self.astonish_client.get_inventory(character.id)
        if not inventory.items:
            await interaction.response.send_message(
                f"{character.markdown()} doesn't own any items.",
                ephemeral=True,
            )
            return

        embeds = [self.presentation.embed_itemstack(item) for item in inventory]
        total = sum(item.stock for item in inventory)
        content = f'{character.markdown()} owns {total} item{"" if total == 1 else "s"}'

        # Don't attempt to show more than 10 itemstack embeds
        if len(embeds) > 10:
            remaining = len(embeds) - 10
            content += f' ({remaining} stack{"" if remaining == 1 else "s"} not shown):'
        else:
            content += ':'

        await interaction.response.send_message(content, embeds=embeds[:10])

    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    async def link_profile(
        self,
        interaction: CelebiInteraction,
        member_to_link: discord.Member,
    ) -> None:
        modal = LinkProfileModal(member_to_link, self.astonish_client)
        await interaction.response.send_modal(modal)

    @app_commands.command()
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    async def extra(
        self,
        interaction: CelebiInteraction,
        character: TransformCharacter,
    ) -> None:
        """
        Shows the extra data attached to an ASTONISH character.

        :param character: The (partial) name or numeric ID of the character whose data to show.
        """
        dumped = character.extra.model_dump_json(indent=2)
        await interaction.response.send_message(f'```json\n{dumped}```')

    @app_commands.command()
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    @app_commands.rename(pkmn='pokemon', custom_sprite_url='sprite')
    async def add_pokemon(
        self,
        interaction: CelebiInteraction,
        pkmn: TransformPokemon,
        character: TransformCharacter,
        shiny: bool = False,
        custom_sprite_url: str | None = None,
    ) -> None:
        """
        Add a Pokémon to a character's team (personal computer).

        :param pkmn: The name or numeric ID of the Pokémon to add.
        :param character: The (partial) name or numeric ID of the character to give the Pokémon to.
        :param shiny: Whether to add the shiny variant of the Pokémon.
        :param custom_sprite_url: The custom sprite URL to use for this Pokémon. If left empty, the official artwork will be used.
        """
        await interaction.response.defer(ephemeral=True)

        # Create the Pokemon embed
        pkmn_embed = await interaction.client.presentation.embed_pokemon(
            pkmn,
            shiny=shiny,
            detailed=False,
        )
        if custom_sprite_url:
            pkmn_embed.set_thumbnail(url=custom_sprite_url)

        # Create the Character embed
        character_embed = interaction.client.presentation.embed_character(
            character,
            detailed=False,
        )

        # Confirm whether we found the proper Pokemon/character to modify
        continuation = await ConfirmationView.display(
            interaction,
            (
                f"You're trying to add **{pkmn_embed.title}** to "
                f"{character.markdown()}'s team. Is this correct?"
            ),
            embeds=[pkmn_embed, character_embed],
        )

        if not continuation:
            return

        await continuation.response.defer()

        # Create and add the Pokemon to the target PC
        character.personal_computer.root.append(
            Pokemon(
                id=pkmn.id,
                name=pokemon_name(
                    await pkmn.forms[0].fetch(),
                    await pkmn.species.fetch(),
                ),
                shiny=shiny,
                custom_sprite_url=custom_sprite_url,  # type: ignore
            )
        )
        await self.astonish_client.update_character(character)

        logger.info(
            "%r added %r (#%d) to character #%d's PC",
            continuation.user.name,
            pkmn.name,
            pkmn.id,
            character.id,
        )

        # Notify the command sender of the outcome
        await continuation.followup.send(
            (
                f'{continuation.user.mention} added a Pokémon '
                f"to {character.markdown()}'s team:"
            ),
            embed=pkmn_embed,
        )

    @app_commands.command()
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    @app_commands.rename(name_or_index='pokemon')
    async def remove_pokemon(
        self,
        interaction: CelebiInteraction,
        name_or_index: str,
        character: TransformCharacter,
    ) -> None:
        """
        Remove a Pokémon from a character's team (personal computer).

        :param name_or_index: The exact name or numeric (1-based) index of the Pokémon to remove.
        :param character: The (partial) name or numeric ID of the character to remove the Pokémon from.
        """
        await interaction.response.defer(ephemeral=True)

        pc = character.personal_computer.root
        index = None

        # Find the index of the Pokemon to remove
        try:
            index = int(name_or_index) - 1  # Convert to 0-indexing
        except ValueError:
            # Find the Pokemon with the exact name as queried
            for i, pkmn in enumerate(pc):
                if pkmn.name.casefold() == name_or_index.casefold():
                    index = i
                    break

        if index is None or not (0 <= index < len(pc)):
            logger.warning(
                "Failed to query PC Pokemon matching %r in character #%r's team",
                name_or_index,
                character.id,
            )

            content = "I couldn't find the Pokémon matching your search."
            await interaction.followup.send(content)
            return

        pkmn = pc[index]

        # Create the Pokemon embed
        pkmn_embed = pkmn.embed()

        # Create the Character embed
        character_embed = interaction.client.presentation.embed_character(
            character,
            detailed=False,
        )

        # Confirm whether we found the proper Pokemon/character to modify
        continuation = await ConfirmationView.display(
            interaction,
            (
                f"You're trying to remove **{pkmn.name}** from "
                f"{character.markdown()}'s team. Is this correct?"
            ),
            embeds=[pkmn_embed, character_embed],
        )

        if not continuation:
            return

        await continuation.response.defer()

        # Remove the Pokemon from the target PC
        pc.pop(index)
        await self.astonish_client.update_character(character)

        logger.info(
            "%r removed %r (#%d) from character #%d's PC",
            continuation.user.name,
            pkmn.name,
            pkmn.id,
            character.id,
        )

        # Notify the command sender of the outcome
        await continuation.followup.send(
            (
                f'{continuation.user.mention} removed a Pokémon '
                f"from {character.markdown()}'s team:"
            ),
            embed=pkmn_embed,
        )


class LinkProfileModal(ui.Modal, title='Link Jcink profile'):
    """
    A modal that is displayed to walk the user through linking
    a :class:`discord.Member` to an ASTONISH (Jcink-hosted) profile.
    """

    url: ui.TextInput = ui.TextInput(
        label='Profile page',
        placeholder='https://astonish.jcink.net/index.php?showuser=173',
    )

    _bad_input_message: ClassVar[str] = (
        'The provided link is not a valid ASTONISH profile URL. '
        'No changes have been made. Please try again.'
    )
    """
    The message to display when profile linkage
    fails due to improper user input.
    """

    def __init__(
        self,
        member_to_link: discord.Member,
        astonish_client: AstonishClient,
    ) -> None:
        super().__init__()
        self.member_to_link = member_to_link
        self.astonish_client = astonish_client

    async def on_submit(self, interaction: CelebiInteraction) -> None:  # type: ignore[override]
        await interaction.response.defer(ephemeral=True, thinking=True)

        # Parse it as a URL
        try:
            profile_url = URL(self.url.value)
            memberid = int(profile_url.query['showuser'])
        except Exception:
            logger.warning('Jcink profile linkage failed', exc_info=True)
            await interaction.followup.send(
                self._bad_input_message,
                ephemeral=True,
            )
            return

        # Make sure it's in the format we expect
        if not (
            profile_url.is_absolute()
            and profile_url.host == 'astonish.jcink.net'
            and profile_url.path == '/index.php'
        ):
            await interaction.followup.send(
                self._bad_input_message,
                ephemeral=True,
            )
            return

        # Do the linking
        try:
            chara = await self.astonish_client.get_character(memberid)
            chara.extra.discord_id = self.member_to_link.id
            await self.astonish_client.update_character(chara)
        except Exception:
            await interaction.followup.send(
                f'Failed to link Jcink profile #{memberid}. '
                'More info may be available in the bot logs.',
                ephemeral=True,
            )
            logger.exception('Failed to link Jcink profile')
        else:
            await interaction.followup.send(
                f'Linked {chara.markdown()} to {self.member_to_link.mention}!',
                ephemeral=True,
            )
            logger.info(
                'Linked profile %r to Discord user %r',
                chara.username,
                str(self.member_to_link),
            )


class PokemonTeamView(EmbedMenu):
    def __init__(
        self,
        original_user: discord.User | discord.Member,
        personal_computer: PersonalComputer,
        presentation: Presentation,
        poke_client: AiopokeClient,
    ) -> None:
        super().__init__(original_user, len(personal_computer))

        self.personal_computer = personal_computer
        self.presentation = presentation
        self.poke_client = poke_client

    async def create_embed(self, index: int, /) -> discord.Embed:
        pkmn = self.personal_computer[index]

        # Generate the default embed
        embed = await self.presentation.embed_pokemon(
            await self.poke_client.get_pokemon(pkmn.id),
            shiny=pkmn.shiny,
        )

        # If this individual Pokemon has a custom sprite configured, use it
        if pkmn.custom_sprite_url:
            embed.set_thumbnail(url=pkmn.custom_sprite_url)

        # Add a position indicator to the footer
        if not embed.footer:
            embed.set_footer(text=f'{index + 1}/{self.count}')

        return embed


async def setup(bot: CelebiClient) -> None:
    await bot.add_cog(AstonishCog(bot))
