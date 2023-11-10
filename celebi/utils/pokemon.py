import random
from typing import Iterable

import aiopoke

__all__ = [
    'localize',
    'display_name',
    'flavor_text',
    'sanitize',
    'height',
    'weight',
]

_INCHES_PER_METER = 1000 / 25.4
_INCHES_PER_FOOT = 12
_POUNDS_PER_KILOGRAM = 1 / 0.45359237


def localize(names: Iterable[aiopoke.Name], language: str) -> str:
    """
    Pick the first :class:`aiopoke.Name` from a list
    that matches ``language``.

    :param names: The names to choose from.
    :param language: The language of the desired text.
    :raises ValueError: If no name matches the language.
    :return: The name with the given language.
    """
    for name in names:
        if name.language.name == language:
            return name.name

    raise ValueError(f'Missing language: {language!r}')


def display_name(name: str, shiny: bool = False) -> str:
    """
    Format a Pokemon's name to make it suitable for user-facing display.

    :param name: The Pokemon name to format.
    :param shiny: Whether to format the shiny variant of the Pokemon.
    :return: The formatted Pokemon name.
    """
    # Replace Mars/Venus symbols with M/F
    name = name.replace('♂', ' M').replace('♀', ' F')

    # Append '(Shiny)' if the Pokemon is shiny
    return f'{name} (Shiny)' if shiny else name


def flavor_text(entries: Iterable[aiopoke.FlavorText], language: str) -> str:
    choices = {e.flavor_text for e in entries if e.language.name == language}

    if not choices:
        raise ValueError(f'Missing language: {language!r}')

    text = random.choice(list(choices))
    return sanitize(text)


def sanitize(text: str, /) -> str:
    # Note: Order matters in this .replace() chain
    return (
        text.replace('-\n', '-')  # Hyphenated newline -> hyphen
        .replace('\u00ad\f', '')  # Delete soft hyphen
        .replace('\u00ad\n', '')  # Delete soft hyphenated newline
        .replace('\n', ' ')  # Delete newline
        .replace('\f', ' ')  # Delete form feed
        .replace('--', '\u2014')  # Double hyphen -> em dash
        .replace('\u2019', "'")  # ASCII-ify fancy apostrophe
    )


def height(meters: float, /) -> str:
    """
    Format a Pokemon height in a similar way as Bulbapedia.

    :param meters: The height to format, in meters.
    :raises ValueError: If meters is not a positive number.
    :return: The formatted height text.
    """
    if meters <= 0:
        raise ValueError('Height must be positive')

    feet, inches = divmod(round(meters * _INCHES_PER_METER), _INCHES_PER_FOOT)

    return f'{feet:0.0f}\'{inches:02.0f}" ({meters:0.01f} m)'


def weight(kilograms: float) -> str:
    """
    Format a Pokemon weight in a similar way as Bulbapedia.

    :param meters: The weight to format, in kilograms.
    :param
    :raises ValueError: If meters is not a positive number.
    :return: The formatted weight text.
    """
    if kilograms <= 0:
        raise ValueError('Weight must be positive')

    # Round before formatting to make sure we format '1 lb' correctly
    pounds = round(kilograms * _POUNDS_PER_KILOGRAM, 1)
    pounds_str = f'{pounds:0.1f} {"lb" if pounds == 1 else "lbs"}.'

    return f'{pounds_str} ({kilograms:0.01f} kg)'
