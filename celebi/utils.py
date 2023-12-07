from __future__ import annotations

import logging
from contextlib import contextmanager, suppress
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
    language: MinimalResource[Language]


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
    form: aiopoke.PokemonForm | None,
    species: aiopoke.PokemonSpecies,
    *,
    language: str = 'en',
) -> str:
    """
    Return the best name for a given Pokemon form and species.

    :param form: The specific Pokemon form, if known.
    :param species: The species of Pokemon.
    :param language: The desired name language.
    :return: The most specific name available for the Pokemon form+species.
    """
    if form is not None:
        with suppress(ValueError):
            return translate_first(form.names, language=language).name

    with suppress(ValueError):
        return translate_first(species.names, language=language).name

    logger.warning(
        'Failed to get suitable name for form %r (species %r)',
        form.name if form is not None else None,
        species.name,
    )
    return species.name.title()


def translate_first(objs: Iterable[TTranslated], language: str) -> TTranslated:
    """
    Choose the first PokeAPI object matching the given language.

    :param objs: The translated objects to choose from.
    :raises ValueError: If an object in the given language was not found.
    :return: The object matching `self.language`.
    """
    return next(translate(objs, language))


def translate(
    objs: Iterable[TTranslated],
    language: str,
) -> Iterator[TTranslated]:
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


@contextmanager
def rewrap_exception(
    from_type: type[BaseException],
    to_type: type[BaseException],
    /,
):
    if not issubclass(to_type, from_type):
        raise TypeError('to_type must be a subtype of from_type')

    try:
        yield
    except from_type as e:
        raise to_type(*e.args) from None
