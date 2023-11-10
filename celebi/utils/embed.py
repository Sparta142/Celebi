import logging

import aiopoke
import discord
import discord.utils
from yarl import URL

from celebi.utils import pokemon as pokemon_utils

LANGUAGE = 'en'

logger = logging.getLogger(__name__)


async def pokemon(
    pkmn: aiopoke.Pokemon,
    guild: discord.Guild,
    shiny: bool = False,
) -> discord.Embed:
    """
    Build a Discord embed for a Pokemon.

    :param pkmn: The Pokemon to embed.
    :param guild: The Discord guild whose emojis to use.
    :param shiny: Whether the Pokemon should display as "shiny".
    :return: The Discord embed
    """
    species = await pkmn.species.fetch()

    # Localize the Pokemon name
    try:
        name = pokemon_utils.localize(species.names, LANGUAGE)
    except ValueError:
        logger.warning('Missing localized name: %r', species)
        name = species.name.title()

    # Pick and localize the flavor text
    try:
        flavor_text = pokemon_utils.flavor_text(
            species.flavor_text_entries,
            LANGUAGE,
        )
    except ValueError:
        logger.warning('Missing flavor text: %r', species)
        flavor_text = ''

    # Build a URL to search for the Pokemon's wiki page
    url = URL('https://bulbapedia.bulbagarden.net') % {'search': name}

    # Build the actual Discord embed
    embed = discord.Embed(
        title=pokemon_utils.display_name(name, shiny),
        description=f'**No. {pkmn.id}**\n{flavor_text}',
        url=url,
    )

    # Add localized type names for this Pokemon
    for typ in pkmn.types:
        natural_gift = await typ.type.fetch()

        try:
            value = pokemon_utils.localize(natural_gift.names, LANGUAGE)
        except ValueError:
            logger.warning('Missing localized name: %r', natural_gift)
            value = natural_gift.name.title()

        emoji_name = f'type{natural_gift.name}'

        if emoji := discord.utils.get(guild.emojis, name=emoji_name):
            embed.add_field(name='Type', value=f'{emoji} {value}')
        else:
            logger.warning('Guild is missing expected emoji: %r', emoji_name)
            embed.add_field(name='Type', value=value)

    # Various other fields
    embed.add_field(name='Rarity', value='???')  # TODO
    embed.add_field(name='Evolution', value='???')  # TODO
    embed.add_field(name='Location', value='???', inline=False)  # TODO
    embed.add_field(name='Weight', value=pokemon_utils.weight(pkmn.weight / 10))
    embed.add_field(name='Height', value=pokemon_utils.height(pkmn.height / 10))

    # Add the Pokemon's official artwork as a thumbnail, if available
    sprites = pkmn.sprites.other

    if sprites:
        if shiny:
            embed.set_thumbnail(url=sprites.official_artwork_front_shiny.url)
        else:
            embed.set_thumbnail(url=sprites.official_artwork_front_default.url)

    # Add attributions and other info
    embed.set_footer(
        text='Data provided by PokéAPI  •  https://pokeapi.co/',
        icon_url='https://pokeapi.co/pokeapi_192_square.png',
    )

    return embed
