from enum import Enum, StrEnum
from functools import cached_property
from typing import TYPE_CHECKING, Annotated, Any, ClassVar, Literal, Self

import aiopoke
import discord
import lxml.etree
import lxml.html
from bs4 import BeautifulSoup, SoupStrainer, Tag
from lxml.html.builder import E
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


class UserMismatchError(Exception):
    pass


class BaseModel(_BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)


class Pokemon(BaseModel):
    id: int = Field(gt=0)
    name: str
    shiny: bool = False
    custom_sprite_url: HttpUrl | None = None

    _pkmn_id_attr: ClassVar[str] = 'data-pkmn-id'

    @property
    def sprite_url(self) -> str:
        if self.custom_sprite_url:
            return str(self.custom_sprite_url)

        return (
            'https://raw.githubusercontent.com'
            '/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork'
            f'{"/shiny" if self.shiny else ""}/{self.id}.png'
        )

    @classmethod
    def from_aiopoke(
        cls,
        pkmn: aiopoke.Pokemon,
        *,
        shiny: bool = False,
    ) -> Self:
        return cls(
            id=pkmn.id,
            name=pkmn.name.title(),  # XXX
            shiny=shiny,
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

            id = None

            if parent.has_attr(cls._pkmn_id_attr):
                id = int(parent.attrs[cls._pkmn_id_attr])

            # Find <div class="pkmn-name">
            name = parent.find('div', class_='pkmn-name', recursive=False)
            assert isinstance(name, Tag)

            # Find <img src="..." />
            img = parent.find('img', src=True, recursive=False)
            assert isinstance(img, Tag)

            src = URL(img.attrs['src'])

            if id is None:
                id = int(src.name.removesuffix(src.suffix))

            results.append(
                cls(
                    id=id,
                    name=name.text,
                    shiny='shiny' in parent.attrs['class'],
                    custom_sprite_url=str(src),
                )
            )

        return results

    def model_dump_html(self) -> str:
        element = E.div(
            {'class': 'pkmn-display', self._pkmn_id_attr: str(self.id)},
            E.i({'class': 'fa-solid fa-sparkles'}, ''),
            E.div({'class': 'pkmn-name'}, self.name),
            E.img({'src': self.sprite_url}),
        )

        return lxml.etree.tostring(
            element,
            encoding='unicode',
            pretty_print=False,
        )


PersonalComputer = Annotated[
    list[Pokemon],
    BeforeValidator(Pokemon.parse_all_html),
]


class DescEnum(Enum):
    def __new__(cls, *args, **kwargs):
        obj = object.__new__(cls)
        obj._value_ = args[0]
        return obj

    def __init__(self, _, description: str = '') -> None:
        self.__description = description

    def __str__(self) -> str:
        return self.description

    @property
    def description(self) -> str:
        return self.__description


class BloodType(DescEnum):
    MORTAL = 'mo', 'Mortal'
    METIC = 'me', 'Metic'
    HEMITHEO = 'he', 'Hemitheo'


InamorataStatus = Annotated[
    bool,
    BeforeValidator(lambda s: {'n': False, 'y': True}[s]),
    PlainSerializer(lambda x: 'y' if x else 'n'),
]

TimeZoneOffset = Annotated[
    int,
    PlainSerializer(lambda x: '0' if x == 0 else f'{x:+}'),
]


class ContactMethod(DescEnum):
    TAGS = 'tag', 'Tags'
    MESSAGES = 'dms', 'Messages'
    TAGS_OR_DMS = 'tdm', 'Tags or DMs'


class MatureContent(DescEnum):
    YES = 'y', 'Yes'
    NO = 'n', 'No'
    ASK = 'a', 'Ask'


class Proficiency(DescEnum):
    NONE = 'n', 'None'
    COMBAT = 'c', 'Combat'
    SURVIVAL = 's', 'Survival'
    POKEMON_KNOWLEDGE = 'pk', 'Pokémon Knowledge'
    POKEMON_HANDLING = 'ph', 'Pokémon Handling'
    HISTORY = 'h', 'History'
    AURA = 'a', 'Aura'
    INSIGHT = 'ins', 'Insight'
    INVESTIGATION = 'inv', 'Investigation'
    INTIMIDATION = 'int', 'Intimidation'
    PERFORMANCE = 'perf', 'Performance'
    STYLING = 'st', 'Styling'
    PERSUASION = 'pers', 'Persuasion'


class TrainerClass(StrEnum):
    APHIDOIDEA = 'aphidoidea'
    KRISIGOS = 'krisigos'
    MNEMNTIA = 'mnemntia'
    SOPHIST = 'sophist'
    STRATEGOS = 'strategos'
    THIARCHOS = 'thiarchos'
    VALIDATING = 'validating'
    """Pseudo trainer class for not-yet-accepted characters."""

    NEREID = 'Nereid'
    """Pseudo trainer class for characters used for test purposes."""

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
            cls.NEREID: 0x5383C6,
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
            return element.text_content()

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
    hover_image: HttpUrl = Field(alias='field_23')
    triggers_and_warnings: Html = Field(alias='field_24')
    personal_computer: PersonalComputer = Field(alias='field_25')
    inamorata_ability: Html = Field(alias='field_26')
    proficiency_1: Proficiency = Field(alias='field_27')
    proficiency_2: Proficiency = Field(alias='field_28')
    proficiency_3: Proficiency = Field(alias='field_29')
    proficiency_4: Proficiency = Field(alias='field_30')
    development_forum: Html = Field(alias='field_31')
    extra: Json['ExtraData'] = Field(alias='field_32')

    @field_validator('extra', mode='wrap')
    @classmethod
    def _validate_extra(
        cls,
        v: Any,
        handler: ValidatorFunctionWrapHandler,
        info,
    ):
        return ExtraDataV1() if v == '' else handler(v)

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
        return is_restricted_group(self.group)

    def trainer_class(self) -> TrainerClass:
        return TrainerClass(self.group)  # Might raise an exception

    def raise_if_restricted(self) -> None:
        if self.restricted:
            raise RestrictedCharacterError(self.username)

    def raise_if_user_mismatch(
        self,
        user: discord.User | discord.Member,
    ) -> None:
        if self.extra.discord_id is None:
            raise UserMismatchError('This character has no linked Discord user')
        elif self.extra.discord_id != user.id:
            raise UserMismatchError(
                'The given Discord user does not match '
                'the one linked to this character'
            )


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
    version: Literal[1] = 1
    discord_id: int | None = None

    model_config = {'arbitrary_types_allowed': True}


ExtraData = Annotated[
    ExtraDataV1,
    Field(discriminator='version'),
]


class MemberCard(BaseModel):
    id: int
    username: str
    flavour_text: str
    group: str
    age: str
    gender_and_pronouns: str
    occupation: str
    face_claim: str
    blood: str
    inamorata: str
    player_name: str

    @classmethod
    def parse_html(cls, element: lxml.html.HtmlElement) -> Self:
        (a,) = element.cssselect('h1 > span > a[href]')
        href = URL(a.attrib['href'])
        (flavour_text,) = element.cssselect('.member-list-flavour-text')
        (basics,) = element.cssselect('ul.member-list-member-basics')
        (group,) = basics.cssselect('li.group:nth-child(1)')
        (age,) = basics.cssselect('li:nth-child(2)')
        (gender,) = basics.cssselect('li:nth-child(3)')
        (occupation,) = basics.cssselect('li.occupation:nth-child(4)')
        (face_claim,) = basics.cssselect('li.face-claim:nth-child(5)')
        (blood,) = basics.cssselect('li.blood:nth-child(6)')
        (inamorata,) = basics.cssselect('li.inamorata:nth-child(7)')
        (player_name,) = element.cssselect('.member-list-played-by > b')

        return cls(
            id=int(href.query['showuser']),
            username=a.text or '',
            flavour_text=flavour_text.text or '',
            group=group.text or '',
            age=age.text or '',
            gender_and_pronouns=gender.text or '',
            occupation=occupation.text or '',
            face_claim=face_claim.text or '',
            blood=blood.text or '',
            inamorata=inamorata.text or '',
            player_name=player_name.text or '',
        )

    @property
    def profile_url(self) -> str:
        return f'https://astonish.jcink.net/index.php?showuser={self.id}'


class ModCPFields(BaseModel):
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
    hover_image: HttpUrl = Field(alias='field_23')
    triggers_and_warnings: Html = Field(alias='field_24')
    personal_computer: PersonalComputer = Field(alias='field_25')
    inamorata_ability: Html = Field(alias='field_26')
    proficiency_1: Proficiency = Field(alias='field_27')
    proficiency_2: Proficiency = Field(alias='field_28')
    proficiency_3: Proficiency = Field(alias='field_29')
    proficiency_4: Proficiency = Field(alias='field_30')
    development_forum: Html = Field(alias='field_31')
    extra: Json['ExtraData'] = Field(alias='field_32')

    @classmethod
    def parse_html(cls, element: lxml.html.FormElement) -> Self:
        return cls.model_validate(element.fields, from_attributes=False)


def is_restricted_group(group: str) -> bool:
    return group not in TrainerClass
