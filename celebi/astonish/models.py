from enum import Enum, StrEnum
from functools import cached_property
from typing import TYPE_CHECKING, Annotated, Any, Literal, Self

import discord
import lxml.etree
import lxml.html
from bs4 import BeautifulSoup, SoupStrainer, Tag
from pydantic import BaseModel as _BaseModel
from pydantic import (
    BeforeValidator,
    ConfigDict,
    Field,
    GetCoreSchemaHandler,
    HttpUrl,
    Json,
    PlainSerializer,
    PositiveInt,
    StrictStr,
    ValidatorFunctionWrapHandler,
    field_validator,
)
from pydantic_core import CoreSchema, core_schema
from yarl import URL

if TYPE_CHECKING:
    from celebi._types import Soupable


class ElementNotFoundError(Exception):
    pass


class RestrictedCharacterError(Exception):
    def __init__(self, username: str) -> None:
        msg = (
            f'The character {username!r} is restricted and '
            'may not be displayed in a public context.'
        )
        super().__init__(msg)


class BaseModel(_BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)


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
    def parse_all_html(cls, markup: 'Soupable') -> list[Self]:
        return cls.parse_all_tag(
            BeautifulSoup(
                markup,
                'lxml',
                parse_only=SoupStrainer(['div', 'img']),
            )
        )

    @classmethod
    def parse_all_tag(cls, tag: Tag) -> list[Self]:
        results = []

        for parent in tag.find_all('div', class_='pkmn-display'):
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
                    name=name.text,
                    shiny='shiny' in parent.attrs['class'],
                )
            )

        return results


PersonalComputer = Annotated[
    list[Pokemon],
    BeforeValidator(Pokemon.parse_all_html),
]


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


class ContactMethod(StrEnum):
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


class MatureContent(StrEnum):
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


class Proficiency(StrEnum):
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


class TrainerClass(StrEnum):
    APHIDOIDEA = 'aphidoidea'
    KRISIGOS = 'krisigos'
    MNEMNTIA = 'mnemntia'
    SOPHIST = 'sophist'
    STRATEGOS = 'strategos'
    THIARCHOS = 'thiarchos'
    VALIDATING = 'validating'
    """Pseudo trainer class for not-yet-accepted characters. """

    def __str__(self) -> str:
        return self.value.title()

    @property
    def color(self) -> int | None:
        cls = type(self)
        return {
            cls.APHIDOIDEA: 0x266C54,
            cls.KRISIGOS: 0x657925,
            cls.MNEMNTIA: 0x2E6F7F,
            cls.SOPHIST: 0x8E681E,
            cls.STRATEGOS: 0xB36B42,
            cls.THIARCHOS: 0x8A56A4,
        }.get(self)


class Html(str):
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type,
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        return core_schema.no_info_after_validator_function(cls, handler(str))

    @cached_property
    def plain_text(self) -> str:
        if self:
            element = lxml.html.fromstring(self)
            return element.text or ''

        return ''


class Character(BaseModel):
    username: StrictStr = Field(exclude=True)
    group: StrictStr = Field(exclude=True)
    id: PositiveInt = Field(strict=True, exclude=True)

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
    personal_computer: PersonalComputer = Field(alias='field_25')
    inamorata_ability: Html = Field(alias='field_26')
    proficiency_1: Proficiency = Field(alias='field_27')
    proficiency_2: Proficiency = Field(alias='field_28')
    proficiency_3: Proficiency = Field(alias='field_29')
    proficiency_4: Proficiency = Field(alias='field_30')
    development_forum: Html = Field(alias='field_31')
    extra: Json['ExtraData'] | None = Field(alias='field_32')

    @field_validator('extra', mode='wrap')
    @classmethod
    def _validate_extra(
        cls,
        v: Any,
        handler: ValidatorFunctionWrapHandler,
        info,
    ):
        return None if v == '' else handler(v)

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

    @property
    def restricted(self) -> bool:
        """
        Whether this character should *not* be shown in
        Discord embeds or similar circumstances.
        """
        return self.group not in TrainerClass

    def trainer_class(self) -> TrainerClass:
        return TrainerClass(self.group)  # Might raise an exception

    def raise_if_restricted(self):
        if self.restricted:
            raise RestrictedCharacterError(self.username)


class ItemStack(BaseModel):
    """Represents a single stack of items owned by a character."""

    icon_url: HttpUrl
    name: StrictStr
    description: StrictStr
    stock: PositiveInt


class Inventory(BaseModel):
    """Represents a character name and all items that character owns."""

    owner: StrictStr
    items: list[ItemStack] = Field(default_factory=list, max_length=10)

    def __iter__(self):
        yield from self.items


class ExtraDataV1(BaseModel):
    version: Literal[1]
    discord_id: Annotated[
        discord.Object,
        BeforeValidator(discord.Object),
        PlainSerializer(lambda obj: obj.id, return_type=int),
    ]

    model_config = {'arbitrary_types_allowed': True}


ExtraData = Annotated[
    ExtraDataV1,
    Field(discriminator='version'),
]
