from typing import Self

from bs4 import BeautifulSoup, Tag
from pydantic import BaseModel, Field
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
    personal_computer: list[Pokemon]
