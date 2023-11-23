import logging
from typing import TYPE_CHECKING, Iterable, Iterator, Protocol, TypeVar

import aiopoke

if TYPE_CHECKING:
    from _typeshed import SupportsAllComparisons
    from aiopoke import Language
    from aiopoke.utils import MinimalResource

logger = logging.getLogger(__name__)


class _HasFullLanguage(Protocol):
    language: Language


class _HasMinimalLanguage(Protocol):
    language: 'MinimalResource[Language]'


HasLanguage = _HasFullLanguage | _HasMinimalLanguage
TTranslated = TypeVar('TTranslated', bound=HasLanguage)
TComparable = TypeVar('TComparable', bound='SupportsAllComparisons')


def clamp(
    x: TComparable,
    lower: TComparable,
    upper: TComparable,
) -> TComparable:
    if x < lower:
        return lower
    elif x > upper:
        return upper

    return x


def pokemon_name(
    form: aiopoke.PokemonForm,
    species: aiopoke.PokemonSpecies,
    *,
    language: str = 'en',
) -> str:
    """
    Return the best name for a given Pokemon form and species.

    :param form: _description_
    :param species: _description_
    :param language: _description_, defaults to 'en'
    :return: _description_
    """
    try:
        return translate_first(form.names, language=language).name
    except ValueError:
        try:
            return translate_first(species.names, language=language).name
        except ValueError:
            logger.warning('Failed to get suitable name for ')
            return species.name.title()


def translate_first(
    objs: Iterable['TTranslated'],
    language: str,
) -> 'TTranslated':
    """
    Choose the first PokeAPI object matching the given language.

    :param objs: The translated objects to choose from.
    :raises ValueError: If an object in the given language was not found.
    :return: The object matching `self.language`.
    """
    return next(translate(objs, language))


def translate(
    objs: Iterable['TTranslated'],
    language: str,
) -> Iterator['TTranslated']:
    """
    Choose the PokeAPI objects matching the given language.

    :param objs: The translated objects to choose from.
    :raises ValueError: If an object in the given language was not found.
    :return: The objects matching `self.language`.
    """
    found = False

    for o in objs:
        if o.language.name == language:
            found = True
            yield o

    if not found:
        raise ValueError(f'Language not found: {language!r}')
