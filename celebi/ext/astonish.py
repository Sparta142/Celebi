from __future__ import annotations as _annotations

import logging
from typing import TYPE_CHECKING, Final

import discord
from discord import app_commands

from celebi.astonish.models import (
    BloodType,
    Character,
    PersonalComputer,
    Pokemon,
    TrainerClass,
)
from celebi.astonish.shop import AstonishShop
from celebi.discord.cog import BaseCog
from celebi.discord.transformers import TransformCharacter, TransformPokemon
from celebi.discord.views import ConfirmationView, EmbedMenu
from celebi.utils import must, pokemon_name

if TYPE_CHECKING:
    from aiopoke import AiopokeClient

    from celebi.astonish.client import AstonishClient
    from celebi.client import CelebiClient, CelebiInteraction
    from celebi.presentation import Presentation

logger = logging.getLogger(__name__)


class AstonishCog(BaseCog['CelebiClient']):
    def __init__(self, bot: CelebiClient) -> None:
        super().__init__(bot)

        # Initialized in .cog_load()
        self._shop: AstonishShop

    @property
    def poke_client(self) -> AiopokeClient:
        return self.bot.poke_client

    @property
    def presentation(self) -> Presentation:
        return self.bot.presentation

    @property
    def astonish_client(self) -> AstonishClient:
        return self.bot.astonish_client

    async def cog_load(self) -> None:
        # Load data from the forum's IBStore
        self._shop = await self.astonish_client.get_shop_data()
        logger.info(
            'Shop data loaded successfully: %d regions, %d baby pokemon, '
            '%d S1 starters, %d S2 starters, %d S3 starters found',
            len(self._shop.regions),
            len(self._shop.baby_pokemon),
            len(self._shop.stage_1_starters),
            len(self._shop.stage_2_starters),
            len(self._shop.stage_3_starters),
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

        await interaction.followup.send(
            content=f'{character.markdown()} has {count} Pokémon on their team:',
            embed=await view.default_embed(),
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

    @app_commands.command()
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    @app_commands.rename(chara='character')
    async def register(
        self,
        interaction: CelebiInteraction,
        member: discord.Member,
        chara: TransformCharacter,
    ) -> None:
        """
        Links a Discord member to a Jcink character.

        :param member: The Discord member who owns the character.
        :param chara: The Jcink character to link to.
        """
        embed = self.presentation.embed_character(chara, detailed=False)
        continuation = await ConfirmationView.display(
            interaction,
            (
                f"You're about to set {chara.markdown()}'s "
                f'Discord user to {member.mention}. Is this correct?'
            ),
            embed=embed,
        )

        if not continuation:
            return

        # Do the linking
        try:
            chara.extra.discord_id = member.id
            await self.astonish_client.update_character(chara)
        except Exception:
            await continuation.response.send_message(
                f'Failed to link Jcink profile #{chara.id}. '
                'More info may be available in the bot logs.',
                ephemeral=True,
            )
            logger.exception('Failed to link Jcink profile')
            return

        # Add and remove roles
        await member.add_roles(
            *get_roles_for_chara(chara, member.guild),
            reason='Added role entitlements based on character registration',
        )
        await member.remove_roles(
            *get_roles_to_remove(member.guild),
            reason='Removed temporary roles due to character registration',
        )

        # Send success message
        await continuation.response.send_message(
            f'Linked {chara.markdown()} to {member.mention}!',
            ephemeral=True,
        )
        logger.info(
            'Linked profile %r to Discord user %r',
            chara.username,
            str(member),
        )

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
                f"You're about to add **{pkmn_embed.title}** to "
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
                f"You're about to remove **{pkmn.name}** from "
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

    @app_commands.command()
    @app_commands.guild_only()
    async def lookup(
        self,
        interaction: CelebiInteraction,
        member: discord.Member | None = None,
    ) -> None:
        """
        Shows the characters linked to a Discord member.

        :param member: The member whose characters to show. If not given, shows your characters.
        """

        # Fallback to showing the command user's characters
        if member is None:
            assert isinstance(interaction.user, discord.Member)
            member = interaction.user

        # Build a list of the member's non-restricted characters, sorted by ID
        charas = sorted(self._user_characters(member), key=lambda c: c.id)
        count = len(charas)

        # Send an ephemeral error message if the member has no characters
        if not count:
            await interaction.response.send_message(
                f'{member.mention} has no characters linked to them.',
                ephemeral=True,
            )
            return

        # Otherwise, send a paginated list view of that member's character(s)
        view = CharacterListView(interaction.user, charas, self.presentation)
        plural = 'character' if count == 1 else 'characters'

        await interaction.response.send_message(
            f'{member.mention} has {count} {plural} linked to them:',
            view=view,
            embed=await view.default_embed(),
        )

    def _user_characters(self, user: discord.User | discord.Member, /):
        id = user.id

        for chara in self.astonish_client.character_cache.values():
            if chara.extra.discord_id == id and not chara.restricted:
                yield chara


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


class CharacterListView(EmbedMenu):
    def __init__(
        self,
        original_user: discord.User | discord.Member,
        charas: list[Character],
        presentation: Presentation,
    ) -> None:
        super().__init__(original_user, len(charas))

        self.charas = charas
        self.presentation = presentation

    async def create_embed(self, index: int, /) -> discord.Embed:
        embed = self.presentation.embed_character(self.charas[index])

        # Add a position indicator to the footer
        if not embed.footer:
            embed.set_footer(text=f'{index + 1}/{self.count}')

        return embed


# TODO: Move this somewhere else
def get_roles_for_chara(chara: Character, guild: discord.Guild):
    get = discord.utils.get
    roles = guild.roles

    role_map: Final = {
        TrainerClass.STRATEGOS: must(get(roles, name='Strategos')),
        TrainerClass.THIARCHOS: must(get(roles, name='Thiarchos')),
        TrainerClass.KRISIGOS: must(get(roles, name='Krisigos')),
        TrainerClass.MNEMNTIA: must(get(roles, name='Mnemntia')),
        TrainerClass.SOPHIST: must(get(roles, name='Sophist')),
        TrainerClass.NEREID: must(get(roles, name='Nereid')),
    }

    yield role_map[chara.trainer_class()]

    if chara.inamorata_status:
        yield must(get(roles, name='Inamorata'))

    if chara.blood_type == BloodType.HEMITHEO:
        yield must(get(roles, name='Hemitheos'))

    yield must(get(roles, name='Members'))


def get_roles_to_remove(guild: discord.Guild):
    yield must(discord.utils.get(guild.roles, name='Guests'))


async def setup(bot: CelebiClient) -> None:
    await bot.add_cog(AstonishCog(bot))
