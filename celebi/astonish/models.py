import warnings
from enum import Enum
from functools import cached_property
from typing import Annotated, Any, Self

from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning, Tag
from pydantic import (
    BaseModel,
    BeforeValidator,
    Field,
    GetCoreSchemaHandler,
    PlainSerializer,
    StrictInt,
    field_validator,
)
from pydantic_core import CoreSchema, core_schema
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


class Html(str):
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        return core_schema.no_info_after_validator_function(cls, handler(str))

    @cached_property
    def plain_text(self) -> str:
        with warnings.catch_warnings(
            action='ignore',
            category=MarkupResemblesLocatorWarning,
        ):
            return BeautifulSoup(self, 'lxml').text


class Member(BaseModel):
    id: StrictInt
    title: Html
    website: Html
    location: Html
    interests: Html
    signature: Html
    full_name: Html = Field(alias='field_1')
    nicknames: Html = Field(alias='field_2')
    age: Html = Field(alias='field_3')
    date_of_birth: Html = Field(alias='field_4')
    gender_and_pronouns: Html = Field(alias='field_5')
    blood_type: BloodType = Field(alias='field_6')
    inamorata_status: InamorataStatus = Field(alias='field_7')
    orientation: Html = Field(alias='field_8')
    marital_status: Html = Field(alias='field_9')
    height: Html = Field(alias='field_10')
    occupation: Html = Field(alias='field_11')
    home_region: Html = Field(alias='field_12')
    face_claim: Html = Field(alias='field_13')
    art_credits: Html = Field(alias='field_14')
    flavour_text: Html = Field(alias='field_15')
    biography: Html = Field(alias='field_16')
    plot_page: Html = Field(alias='field_17')
    player_name: Html = Field(alias='field_18')
    player_pronouns: Html = Field(alias='field_19')
    player_timezone: TimeZoneOffset = Field(alias='field_20')
    preferred_contact_method: ContactMethod = Field(alias='field_21')
    mature_content: MatureContent = Field(alias='field_22')
    hover_image: Html = Field(alias='field_23')
    triggers_and_warnings: Html = Field(alias='field_24')
    personal_computer: Annotated[
        list[Pokemon],
        BeforeValidator(Pokemon.parse_html),
    ] = Field(alias='field_25')
    inamorata_ability: Html = Field(alias='field_26')
    proficiency_1: Proficiency = Field(alias='field_27')
    proficiency_2: Proficiency = Field(alias='field_28')
    proficiency_3: Proficiency = Field(alias='field_29')
    proficiency_4: Proficiency = Field(alias='field_30')
    development_forum: Html = Field(alias='field_31')
    discord_id: int | None = Field(alias='field_32', default=None)

    @field_validator('discord_id', mode='before')
    def _validate_discord_id(cls, v: str) -> int | None:
        return int(v) if v else None

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
