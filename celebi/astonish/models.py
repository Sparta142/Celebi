from enum import Enum
from typing import Annotated, Self

from bs4 import BeautifulSoup, Tag
from pydantic import (
    BaseModel,
    BeforeValidator,
    Field,
    PlainSerializer,
    StrictInt,
    field_validator,
)
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


class BloodType(Enum):
    MORTAL = 'mo'
    METIC = 'me'
    HEMITHEO = 'he'

    def __str__(self) -> str:
        cls = type(self)
        return {
            cls.MORTAL: 'Mortal',
            cls.METIC: 'Metic',
            cls.HEMITHEO: 'Hemitheo',
        }[self]


InamorataStatus = Annotated[
    bool,
    BeforeValidator(lambda s: {'n': False, 'y': True}[s]),
    PlainSerializer(lambda x: 'y' if x else 'n'),
]

TimeZoneOffset = Annotated[
    int,
    PlainSerializer(lambda x: '0' if x == 0 else f'{x:+}'),
]


class ContactMethod(Enum):
    TAGS = 'tag'
    MESSAGES = 'dms'
    TAGS_OR_DMS = 'tdm'

    def __str__(self) -> str:
        cls = type(self)
        return {
            cls.TAGS: 'Tags',
            cls.MESSAGES: 'Messages',
            cls.TAGS_OR_DMS: 'Tags or DMs',
        }[self]


class MatureContent(Enum):
    YES = 'y'
    NO = 'n'
    ASK = 'a'

    def __str__(self) -> str:
        cls = type(self)
        return {
            cls.YES: 'Yes',
            cls.NO: 'No',
            cls.ASK: 'Ask',
        }[self]


class Proficiency(Enum):
    NONE = 'n'
    COMBAT = 'c'
    SURVIVAL = 's'
    POKEMON_KNOWLEDGE = 'pk'
    POKEMON_HANDLING = 'ph'
    HISTORY = 'h'
    AURA = 'a'
    INSIGHT = 'ins'
    INVESTIGATION = 'inv'
    INTIMIDATION = 'int'
    PERFORMANCE = 'perf'
    STYLING = 'st'
    PERSUASION = 'pers'

    def __str__(self) -> str:
        cls = type(self)
        return {
            cls.NONE: 'None',
            cls.COMBAT: 'Combat',
            cls.SURVIVAL: 'Survival',
            cls.POKEMON_KNOWLEDGE: 'Pokémon Knowledge',
            cls.POKEMON_HANDLING: 'Pokémon Handling',
            cls.HISTORY: 'History',
            cls.AURA: 'Aura',
            cls.INSIGHT: 'Insight',
            cls.INVESTIGATION: 'Investigation',
            cls.INTIMIDATION: 'Intimidation',
            cls.PERFORMANCE: 'Performance',
            cls.STYLING: 'Styling',
            cls.PERSUASION: 'Persuasion',
        }[self]


class Member(BaseModel):
    id: StrictInt
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
    blood_type: BloodType = Field(alias='field_6')
    inamorata_status: InamorataStatus = Field(alias='field_7')
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
    player_timezone: TimeZoneOffset = Field(alias='field_20')
    preferred_contact_method: ContactMethod = Field(alias='field_21')
    mature_content: MatureContent = Field(alias='field_22')
    hover_image: str = Field(alias='field_23')
    triggers_and_warnings: str = Field(alias='field_24')
    personal_computer: list[Pokemon] = Field(alias='field_25')
    inamorata_ability: str = Field(alias='field_26')
    proficiency_1: Proficiency = Field(alias='field_27')
    proficiency_2: Proficiency = Field(alias='field_28')
    proficiency_3: Proficiency = Field(alias='field_29')
    proficiency_4: Proficiency = Field(alias='field_30')
    development_forum: str = Field(alias='field_31')

    @field_validator('personal_computer', mode='before')
    def _validate_personal_computer(cls, v: str) -> list[Pokemon]:
        return Pokemon.parse_html(v)

    @property
    def profile_url(self) -> str:
        return f'https://astonish.jcink.net/index.php?showuser={self.id}'

    @property
    def proficiencies(self) -> list[Proficiency]:
        candidates = [
            self.proficiency_1,
            self.proficiency_2,
            self.proficiency_3,
            self.proficiency_4,
        ]
        return [p for p in candidates if p != Proficiency.NONE]
