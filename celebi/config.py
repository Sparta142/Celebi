from typing import Literal

from pydantic import BaseModel

from celebi.presentation import PresentationConfig

PokemonType = Literal[
    'Bug',
    'Dark',
    'Electric',
    'Fighting',
    'Fire',
    'Flying',
    'Ghost',
    'Grass',
    'Ground',
    'Ice',
    'Normal',
    'Poison',
    'Psychic',
    'Rock',
    'Steel',
    'Water',
]


class Region(BaseModel):
    name: str
    description: str
    common: list[PokemonType]
    rare: list[PokemonType]


class Config(BaseModel):
    regions: dict[str, Region] = {}
    presentation: PresentationConfig
