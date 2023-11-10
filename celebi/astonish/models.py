from typing import Self

from bs4 import BeautifulSoup, Tag
from pydantic import BaseModel, Field, field_validator
from yarl import URL


class Pokemon(BaseModel):
    id: int = Field(gt=0)
    name: str
    shiny: bool = False

    @property
    def sprite_url(self) -> str:
        return (
            'https://raw.githubusercontent.com'
            '/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork'
            f'{"/shiny" if self.shiny else ""}/{self.id}.png'
        )

    @classmethod
    def parse_html(cls, html: str) -> list[Self]:
        soup = BeautifulSoup(html, 'lxml')
        results = []

        for parent in soup.find_all('div', class_='pkmn-display'):
            assert isinstance(parent, Tag)

            # Find <div class="pkmn-name">
            name = parent.find('div', class_='pkmn-name', recursive=False)
            assert isinstance(name, Tag)

            # Find <img src="..." />
            img = parent.find('img', src=True, recursive=False)
            assert isinstance(img, Tag)

            src = URL(img.attrs['src'])
            stem = src.name.removesuffix(src.suffix)

            results.append(
                cls(
                    id=int(stem),
                    name=name.text.strip(),
                    shiny='shiny' in parent.attrs['class'],
                )
            )

        return results


class Member(BaseModel):
    title: str
    website: str
    location: str
    interests: str
    signature: str
    full_name: str = Field(alias='field_1')
    nicknames: str = Field(alias='field_2')
    age: str = Field(alias='field_3')
    date_of_birth: str = Field(alias='field_4')
    gender_and_pronouns: str = Field(alias='field_5')

    # TODO: Missing fields 6-7

    orientation: str = Field(alias='field_8')
    marital_status: str = Field(alias='field_9')
    height: str = Field(alias='field_10')
    occupation: str = Field(alias='field_11')
    home_region: str = Field(alias='field_12')
    face_claim: str = Field(alias='field_13')
    art_credits: str = Field(alias='field_14')
    flavour_text: str = Field(alias='field_15')
    biography: str = Field(alias='field_16')
    plot_page: str = Field(alias='field_17')
    player_name: str = Field(alias='field_18')
    player_pronouns: str = Field(alias='field_19')

    # TODO: Missing fields 20-24

    personal_computer: list[Pokemon] = Field(alias='field_25')
    inamorata_ability: str = Field(alias='field_26')

    # TODO: Missing fields 27-30

    development_forum: str = Field(alias='field_31')

    @field_validator('personal_computer', mode='after')
    def _validate_personal_computer(cls, v: str) -> list[Pokemon]:
        return Pokemon.parse_html(v)
