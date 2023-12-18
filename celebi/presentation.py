import logging
import random
from contextlib import suppress
from typing import TYPE_CHECKING, Annotated

import discord
from aiopoke import Pokemon, PokemonSpecies
from pydantic import BaseModel, PlainSerializer, PlainValidator, StrictStr
from yarl import URL

from celebi.astonish.models import Character, ItemStack
from celebi.utils import pokemon_name, translate, translate_first

if TYPE_CHECKING:
    from celebi.astonish.client import AstonishClient

logger = logging.getLogger(__name__)

Color = Annotated[
    discord.Colour,
    PlainValidator(discord.Colour),
    PlainSerializer(lambda c: c.value),
]

_INCHES_PER_METER = 1000 / 25.4
_INCHES_PER_FOOT = 12
_POUNDS_PER_KILOGRAM = 1 / 0.45359237


class PresentationConfig(BaseModel):
    language: str = 'en'
    """The PokeAPI language to use."""

    colors: dict[str, Color]

    # Rules to apply when formatting Pokemon embeds
    weight_format: StrictStr
    height_format: StrictStr
    shiny_format: StrictStr


class Presentation:
    def __init__(
        self,
        config: PresentationConfig,
        guild: discord.Guild,
        astonish_client: AstonishClient,
    ) -> None:
        self.config = config
        self.guild = guild
        self.astonish_client = astonish_client

    @property
    def language(self) -> str:
        return self.config.language

    def embed_character(
        self,
        character: Character,
        *,
        detailed: bool = True,
    ) -> discord.Embed:
        """
        Generate a :class:`discord.Embed` describing an ASTONISH character.

        :param character: The character to embed.
        :param detailed: Whether to add lots of details to the embed.
        :return: The embed.
        """
        if character.restricted:
            raise ValueError('Restricted characters may not be embedded')

        if character.flavour_text:
            description = f'>>> *{character.flavour_text.plain_text}*'
        else:
            description = None

        embed = discord.Embed(
            title=character.username,
            url=character.profile_url,
            description=description,
            color=character.trainer_class().color,
        )

        embed.set_thumbnail(url=character.hover_image)
        embed.set_author(
            name='ASTONISH',
            url='https://astonish.jcink.net/',
            icon_url='https://cdn.discordapp.com/icons/1143929947132538931/df2d24f751203a91585ad112a39edb1a.png',
        )

        if detailed:
            embed.add_field(
                name='Gender',
                value=character.gender_and_pronouns.plain_text,
            )
            embed.add_field(
                name='Age',
                value=character.age.plain_text,
            )
            embed.add_field(
                name='Birthday',
                value=character.date_of_birth.plain_text,
            )
            embed.add_field(
                name='Home Region',
                value=character.home_region.plain_text,
            )
            embed.add_field(
                name='Trainer Class',
                value=str(character.trainer_class()),
            )
            embed.add_field(
                name='Blood Type',
                value=str(character.blood_type),
            )
            embed.add_field(
                name='Occupation',
                value=character.occupation.plain_text,
                inline=False,
            )
            embed.add_field(
                name='Proficiencies',
                value=', '.join(str(p) for p in character.proficiencies),
                inline=False,
            )

        return embed

    def embed_itemstack(self, itemstack: ItemStack) -> discord.Embed:
        if itemstack.stock > 1:
            title = f'{itemstack.name} (x{itemstack.stock})'
        else:
            title = itemstack.name

        embed = discord.Embed(title=title, description=itemstack.description)
        embed.set_thumbnail(url=itemstack.icon_url)

        return embed

    # TODO: Add LFU caching to this?
    async def embed_pokemon(
        self,
        pkmn: Pokemon,
        *,
        shiny: bool = False,
        detailed: bool = True,
    ) -> discord.Embed:
        pkmn_form = await pkmn.forms[0].fetch()  # XXX: Is .forms[0] correct?
        species = await pkmn.species.fetch()

        # Translate the specific Pokemon form name
        name = pokemon_name(pkmn_form, species, language=self.language)

        # Convert Mars/Venus symbols to M/F, respectively
        display_name = name.replace('♂', ' M').replace('♀', 'F')

        # Reformat as shiny if necessary
        if shiny:
            display_name = self.config.shiny_format.format(display_name)

        # Randomly pick and translate a flavor text to display
        try:
            flavor_text = self.flavor_text(species)
        except ValueError:
            logger.warning('Missing flavor text: %r', species.name)
            flavor_text = ''

        # Get the color to accent the embed with
        try:
            color = self.pokedex_color(species)
        except KeyError:
            logger.warning('Missing mapped color: %r', species.name)
            color = None

        # Build the actual Discord embed
        embed = discord.Embed(
            title=display_name,
            description=f'**No. {pkmn.id}**\n{flavor_text}',
            url=self.wiki_search_url(species.name),
            color=color,
        )

        if detailed:
            # Add localized type names for this Pokemon
            for typ in pkmn.types:
                natural_gift = await typ.type.fetch()

                try:
                    value = translate_first(
                        natural_gift.names,
                        self.language,
                    ).name
                except ValueError:
                    logger.warning('Missing localized name: %r', natural_gift)
                    value = natural_gift.name.title()

                emoji_name = f'type{natural_gift.name}'
                emoji = discord.utils.get(self.guild.emojis, name=emoji_name)

                if emoji is not None:
                    embed.add_field(name='Type', value=f'{emoji} {value}')
                else:
                    logger.warning(
                        'Guild %r is missing expected emoji: %r',
                        self.guild.name,
                        emoji_name,
                    )
                    embed.add_field(name='Type', value=value)

            # Add various other fields
            embed.add_field(name='Rarity', value='???')  # TODO
            embed.add_field(name='Evolution', value='???')  # TODO
            embed.add_field(name='Location', value='???', inline=False)  # TODO
            embed.add_field(name='Weight', value=self.weight(pkmn.weight / 10))
            embed.add_field(name='Height', value=self.height(pkmn.height / 10))

        # Add the Pokemon sprite as a thumbnail, if available
        if thumbnail_url := self.sprite(pkmn, shiny):
            embed.set_thumbnail(url=thumbnail_url)

        embed.set_author(
            name='PokéAPI',
            url='https://pokeapi.co/',
            icon_url='https://pokeapi.co/pokeapi_192_square.png',
        )

        return embed

    def flavor_text(
        self,
        species: PokemonSpecies,
    ) -> str:
        entries = translate(species.flavor_text_entries, self.language)
        options = set(e.flavor_text for e in entries)
        return sanitize_text(random.choice(list(options)))

    def wiki_search_url(self, query: str, /) -> str:
        url = URL('https://bulbapedia.bulbagarden.net') % {'search': query}
        return str(url)

    def pokedex_color(self, species: PokemonSpecies, /) -> discord.Color:
        return self.config.colors[species.color.name]

    def weight(self, kilograms: float, /) -> str:
        if kilograms < 0:
            raise ValueError('Weight must be non-negative')

        return self.config.weight_format.format(
            kilograms=kilograms,
            grams=kilograms / 1000,
            pounds=kilograms * _POUNDS_PER_KILOGRAM,
        )

    def height(self, meters: float, /) -> str:
        if meters < 0:
            raise ValueError('Height must be non-negative')

        feet, inches = divmod(
            round(meters * _INCHES_PER_METER),
            _INCHES_PER_FOOT,
        )

        return self.config.height_format.format(
            meters=meters,
            centimeters=meters / 100,
            feet=feet,
            inches=inches,
        )

    @staticmethod
    def sprite(pkmn: Pokemon, shiny: bool):
        other = pkmn.sprites.other
        if not other:
            return None

        sprites = [
            other.official_artwork_front_default,
            other.official_artwork_front_shiny,
        ]

        if shiny:
            sprites.reverse()

        for sprite in sprites:
            with suppress(AttributeError):  # `url` can be undefined
                return sprite.url

        return None


def sanitize_text(string: str, /) -> str:
    # Note: Order matters in this .replace() chain
    return (
        string.replace('-\n', '-')  # Hyphenated newline -> hyphen
        .replace('\u00ad\f', '')  # Delete soft hyphen
        .replace('\u00ad\n', '')  # Delete soft hyphenated newline
        .replace('\n', ' ')  # Delete newline
        .replace('\f', ' ')  # Delete form feed
        .replace('--', '\u2014')  # Double hyphen -> em dash
        .replace('\u2019', "'")  # ASCII-ify fancy apostrophe
    )
