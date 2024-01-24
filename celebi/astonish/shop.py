from __future__ import annotations as _annotations

import re
from enum import IntEnum
from typing import Final, Iterator, Self

import lxml.html
from frozendict import frozendict
from pydantic import ConfigDict, StrictStr

from celebi.astonish.models import BaseModel

__all__ = [
    'AstonishShop',
    'Region',
]


class FrozenBaseModel(BaseModel):
    model_config = ConfigDict(frozen=True)


class AstonishShop(FrozenBaseModel):
    regions: tuple[Region, ...]
    baby_pokemon: frozenset[str]
    stage_1_starters: frozenset[str]
    stage_2_starters: frozenset[str]
    stage_3_starters: frozenset[str]

    @classmethod
    def parse_html(cls, element: lxml.html.HtmlElement) -> Self:
        # First find the string that would have been inserted
        # into the page as HTML if JavaScript were active.
        for script in element.cssselect('body > script'):
            if match := re.search(
                r'catchingIndex\.innerHTML\s*=\s*"(?P<html>.+)";',
                script.text or '',
            ):
                fragments = lxml.html.fragments_fromstring(match.group('html'))
                element = lxml.html.HtmlElement(*fragments)
                break
        else:
            raise ValueError('HTML injection script not found')

        # Parse the regions as HTML
        regions = tuple(
            Region.parse_html(child)
            for child in element.cssselect(
                '#catchable-pkmn-content >'
                '.catchable-region:not(.baby):not(.starter)'
            )
        )

        # Parse the '.baby' div
        (baby_pokemon,) = element.cssselect('.catchable-region.baby > div')

        # Parse the '.starter' divs
        starter_elems = element.cssselect('.catchable-region.starter')

        def _select_section(title: str, /) -> Iterator[lxml.html.HtmlElement]:
            for e in starter_elems:
                (span,) = e.cssselect('span.region-title')
                if span.text == title:
                    yield from e.cssselect('* > div')

        (stage_1_starters,) = _select_section('Stage 1 Starters')
        (stage_2_starters,) = _select_section('Stage 2 Starters')
        (stage_3_starters,) = _select_section('Stage 3 Starters')

        def _split(elem: lxml.html.HtmlElement) -> frozenset[str]:
            return frozenset(
                s.strip().lower() for s in elem.text_content().split(',')
            )

        return cls(
            regions=regions,
            baby_pokemon=_split(baby_pokemon),
            stage_1_starters=_split(stage_1_starters),
            stage_2_starters=_split(stage_2_starters),
            stage_3_starters=_split(stage_3_starters),
        )


class Region(FrozenBaseModel):
    name: StrictStr
    types: frozendict[str, Rarity]

    model_config = ConfigDict(arbitrary_types_allowed=True)  # frozendict

    @classmethod
    def parse_html(cls, element: lxml.html.HtmlElement) -> Self:
        (title,) = element.cssselect('.region-title')
        types = {}

        for child in element.cssselect('span.type'):
            t = _PokemonType.parse_html(child)

            if t.name in types:
                raise ValueError(f'Non-unique PokemonType: {t!r}')

            types[t.name] = t.rarity

        return cls(
            name=title.text_content(),
            types=frozendict(types),
        )

    def contains_type(self, type: str) -> bool:
        return type in self.types


class Rarity(IntEnum):
    COMMON = 0
    RARE = 1


class _PokemonType(FrozenBaseModel):
    name: StrictStr
    rarity: Rarity = Rarity.COMMON

    _rare_suffix: Final = '*'
    """The suffix a rare Pokemon type has when displayed on the website."""

    @classmethod
    def parse_html(cls, element: lxml.html.HtmlElement) -> Self:
        if not (name := element.text):
            raise ValueError('Name must not be empty or missing')

        name = name.strip().lower()
        rare = name.endswith(cls._rare_suffix)

        return cls(
            name=name.removesuffix(cls._rare_suffix),
            rarity=Rarity.RARE if rare else Rarity.COMMON,
        )
