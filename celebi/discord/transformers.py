from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

import aiohttp
import aiopoke
import rapidfuzz
from discord.app_commands import Choice, Transform, Transformer

from celebi.astonish.models import is_restricted_group
from celebi.utils import rewrap_exception

if TYPE_CHECKING:
    from celebi.astonish.models import Character, MemberCard
    from celebi.client import CelebiInteraction

__all__ = [
    'PokemonTransformer',
    'CharacterTransformer',
    'TransformPokemon',
    'TransformCharacter',
    'PokemonNotFoundError',
    'CharacterNotFoundError',
]


class PokemonNotFoundError(ValueError):
    pass


class CharacterNotFoundError(ValueError):
    pass


class PokemonTransformer(Transformer):
    _translations = str.maketrans(
        {
            '♂': 'm',
            '♀': 'f',
            ' ': '-',
            '_': '-',
            "'": '',
        }
    )

    _transformations = {
        re.compile(r'^galar(?:ian)?[\s_-](.+)$'): r'\1-galar',
        re.compile(r'^hisui(?:an)?[\s_-](.+)$'): r'\1-hisui',
        re.compile(r'^paldea(?:n)?[\s_-](.+)$'): r'\1-paldea',
        re.compile(r'^alola(?:n)[\s_-](.+)$'): r'\1-alola',
    }

    def __init__(self) -> None:
        self.__all_pokemon: list[str] | None = None

    async def transform(
        self,
        interaction: CelebiInteraction,
        value: Any,
    ) -> aiopoke.Pokemon:
        name_or_id: int | str

        try:
            name_or_id = int(value)
        except ValueError:
            name_or_id = self.sanitize_query(value)

        client = interaction.client.poke_client

        with rewrap_exception(ValueError, PokemonNotFoundError):
            return await client.get_pokemon(name_or_id)

    async def autocomplete(
        self,
        interaction: CelebiInteraction,
        value: int | float | str,
    ) -> list[Choice[int | float | str]]:
        value = str(value)

        if not value:
            return []

        # Find the closest matches for the query
        matches = rapidfuzz.process.extract(
            self.sanitize_query(value),
            await self._all_pokemon(),
            scorer=rapidfuzz.fuzz.partial_ratio,
            processor=rapidfuzz.utils.default_process,
            score_cutoff=70,
            limit=10,
        )

        # Limit the number of matches, then sort by similarity and alphabetically
        matches.sort(key=lambda m: (-m[1], m[0]))

        return [Choice(name=s, value=s) for (s, _, _) in matches]

    @classmethod
    def sanitize_query(cls, value: str) -> str:
        sanitized = value.casefold().translate(cls._translations)

        for pattern, repl in cls._transformations.items():
            sanitized = pattern.sub(repl, sanitized)

        return sanitized

    # TODO: This should be passed into the transformer in __init__
    async def _all_pokemon(self) -> list[str]:
        if self.__all_pokemon is not None:
            return self.__all_pokemon

        async with (
            aiohttp.ClientSession() as session,
            session.get(
                'https://pokeapi.co/api/v2/pokemon',
                params={'limit': 100000, 'offset': 0},
            ) as response,
        ):
            response.raise_for_status()
            data = await response.json()

        self.__all_pokemon = [r['name'] for r in data.get('results', [])]
        return self.__all_pokemon


class CharacterTransformer(Transformer):
    def __init__(self) -> None:
        super().__init__()
        self.__characters: dict[int, MemberCard] | None = None

    async def transform(
        self,
        interaction: CelebiInteraction,
        value: Any,
    ) -> Character:
        try:
            memberid = int(value)
        except ValueError:
            member_cards = await self._characters(interaction)
            extraction = rapidfuzz.process.extractOne(
                value,
                {k: v.username for k, v in member_cards.items()},
                scorer=_similarity,
                processor=rapidfuzz.utils.default_process,
                score_cutoff=0.6,
            )

            # If extraction is falsy/None, then we got no suggestions
            if not extraction:
                msg = f'Could not find a character matching {value!r}'
                raise CharacterNotFoundError(msg)

            # Otherwise, the best-matching member ID is the 3rd tuple element
            memberid = extraction[2]
            assert isinstance(memberid, int)

        ac = interaction.client.astonish_client

        with rewrap_exception(ValueError, CharacterNotFoundError):
            return await ac.get_character(memberid)

    async def autocomplete(
        self,
        interaction: CelebiInteraction,
        value: int | float | str,
    ) -> list[Choice[str | int | float]]:
        member_cards = await self._characters(interaction)

        try:
            card = member_cards[int(value)]
        except (KeyError, ValueError):
            pass  # It's not a member ID; just keep going
        else:
            # Return a single choice with the member with the requested ID,
            # additionally displaying the ID next to the member name.
            return [
                Choice(
                    name=f'{card.username} (#{card.id})',
                    value=str(card.id),
                )
            ]

        # Coerce it to str (empty strings are not autocompleted)
        if not (value := str(value)):
            return []

        matches = rapidfuzz.process.extract(
            value,
            {k: v.username for k, v in member_cards.items()},
            scorer=_similarity,
            processor=rapidfuzz.utils.default_process,
            score_cutoff=0.6,
            limit=3,
        )
        return [Choice(name=str(v), value=str(k)) for (v, _, k) in matches]

    async def _characters(
        self,
        interaction: CelebiInteraction,
    ) -> dict[int, MemberCard]:
        if self.__characters is None:
            ac = interaction.client.astonish_client
            self.__characters = {
                k: v
                for k, v in (await ac.get_all_characters()).items()
                if not is_restricted_group(v.group)
            }

        return self.__characters


def _similarity(*args, score_cutoff: float, **kwargs) -> float:
    jw_similarity = rapidfuzz.distance.JaroWinkler.normalized_similarity(
        *args,
        **kwargs,
        prefix_weight=0.2,
    )

    pts_ratio = rapidfuzz.fuzz.partial_token_set_ratio(
        *args,
        score_cutoff=score_cutoff * 100,
        **kwargs,
    )

    indel_similarity = rapidfuzz.distance.Indel.normalized_similarity(
        *args,
        **kwargs,
    )

    return sum(
        [
            0.35 * jw_similarity,
            0.55 * pts_ratio / 100,
            0.1 * indel_similarity,
        ]
    )


TransformPokemon = Transform[aiopoke.Pokemon, PokemonTransformer]
TransformCharacter = Transform['Character', CharacterTransformer]
