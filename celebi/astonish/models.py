# pyright: reportArgumentType=false

from enum import Enum, StrEnum
from functools import cached_property
from typing import Annotated, Any, Final, Iterator, Literal, Self

import discord
import lxml.etree
import lxml.html
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
    StrictBool,
    StrictStr,
    ValidatorFunctionWrapHandler,
    WrapValidator,
    field_validator,
)
from pydantic_core import CoreSchema, core_schema
from yarl import URL

OptionalHttpUrl = Annotated[
    HttpUrl | None,
    WrapValidator(lambda v, handler: None if not v else handler(v)),
]


class BaseModel(_BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        from_attributes=False,
        str_strip_whitespace=True,
    )


class Pokemon(BaseModel):
    id: PositiveInt
    name: StrictStr
    shiny: StrictBool = False
    custom_sprite_url: OptionalHttpUrl = None

    _pkmn_id_attr: Final = 'data-pkmn-id'

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
    def parse_html(cls, element: lxml.html.HtmlElement) -> Self:
        (img,) = element.cssselect('img[src]')
        src = URL(img.attrib['src'])

        # If it has a Pokemon ID override, use that, otherwise
        # try to parse it out of the <img> src attribute.
        try:
            id = int(element.attrib[cls._pkmn_id_attr])
        except KeyError:
            id = int(src.name.removesuffix(src.suffix))

        (pkmn_name,) = element.cssselect('div.pkmn-name')

        return cls(
            id=id,
            name=pkmn_name.text_content(),
            shiny='shiny' in element.attrib.get('class', []),
            custom_sprite_url=str(src),
        )

    def model_dump_html(self) -> str:
        element = E.div(
            {
                'class': f'pkmn-display{" shiny" if self.shiny else ""}',
                self._pkmn_id_attr: str(self.id),
            },
            E.i({'class': 'fa-solid fa-sparkles'}, ''),
            E.div({'class': 'pkmn-name'}, self.name),
            E.img({'src': self.sprite_url}),
        )

        return lxml.etree.tostring(
            element,
            encoding='unicode',
            pretty_print=False,
        )

    def embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=f'{self.name} (Shiny)' if self.shiny else self.name,
            description=f'**No. {self.id}**',
        )
        embed.set_thumbnail(url=self.sprite_url)
        return embed


class PersonalComputer(BaseModel):
    root: list[Pokemon]

    @classmethod
    def parse_html(cls, element: lxml.html.HtmlElement) -> Self:
        root = [
            Pokemon.parse_html(elem)
            for elem in element.cssselect(
                '.Computer > #biography-body > .pkmn-display'
            )
        ]
        return cls(root=root)

    def __iter__(self) -> Iterator[Pokemon]:  # type: ignore[override]
        return iter(self.root)

    def __len__(self) -> int:
        return len(self.root)

    def __getitem__(self, item: int) -> Pokemon:
        return self.root[item]

    def model_dump_html(self) -> str:
        return ''.join(pkmn.model_dump_html() for pkmn in self)


class DescEnum(Enum):
    def __new__(cls, *args: Any, **kwargs: Any):
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

    # Basic proficiencies
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

    # Master proficiencies
    COMBAT_MASTERY = 'cm', 'Combat Mastery'
    SURVIVAL_MASTERY = 'sm', 'Survival Mastery'
    POKEMON_KNOWLEDGE_MASTERY = 'pkm', 'Pokémon Knowledge Mastery'
    POKEMON_HANDLING_MASTERY = 'phm', 'Pokémon Handling Mastery'
    HISTORY_MASTERY = 'hm', 'History Mastery'
    AURA_MASTERY = 'am', 'Aura Mastery'
    INSIGHT_MASTERY = 'insm', 'Insight Mastery'
    INVESTIGATION_MASTERY = 'invm', 'Investigation Mastery'
    INTIMIDATION_MASTERY = 'intm', 'Intimidation Mastery'
    PERFORMANCE_MASTERY = 'perfm', 'Performance Mastery'
    STYLING_MASTERY = 'stm', 'Styling Mastery'
    PERSUASION_MASTERY = 'persm', 'Persuasion Mastery'


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

    title: Html = Field()
    website: Html = Field()
    location: Html = Field()
    interests: Html = Field()
    signature: Html = Field()
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
    hover_image: OptionalHttpUrl = Field(alias='field_23')
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

    @field_validator('personal_computer', mode='before')
    @classmethod
    def _validate_personal_computer(cls, v: str) -> PersonalComputer:
        return PersonalComputer(
            root=[
                Pokemon.parse_html(elem)
                for elem in lxml.html.fragments_fromstring(v)
            ]
        )

    def markdown(self, *, link: bool = True) -> str:
        """
        Generate Markdown text describing the character,
        optionally including a hyperlink to their profile page.

        :param link: Whether to include a link to the character's profile.
        :return: The Markdown text.
        """
        username = discord.utils.escape_markdown(self.username)

        if link:
            return f'**[{username}]({self.profile_url})**'
        else:
            return f'**{username}**'

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


class ItemStack(BaseModel):
    """Represents a single stack of items owned by a character."""

    icon_url: HttpUrl
    name: StrictStr
    description: StrictStr
    stock: PositiveInt

    @classmethod
    def parse_html(cls, element: lxml.html.HtmlElement) -> Self:
        icon_td, name_td, description_td, stock_td = element.findall('td')
        img = icon_td.find('img')

        if img is None:
            raise ValueError('Missing <img> tag for item icon')

        return cls(
            icon_url=img.attrib['src'],
            name=name_td.text_content(),
            description=description_td.text_content(),
            stock=stock_td.text_content(),
        )


class Inventory(BaseModel):
    """Represents a character name and all items that character owns."""

    owner: StrictStr
    items: list[ItemStack] = Field(default_factory=list)

    @classmethod
    def parse_html(cls, element: lxml.html.HtmlElement) -> Self:
        (table,) = element.cssselect('#ucpcontent > table')
        (owner,) = table.cssselect('tr:nth-child(1) > td:nth-child(2) > a')

        trs = table.cssselect('tr')[3:]
        items: list[ItemStack] = []

        if trs[0].text_content().strip() != 'Inventory Empty.':
            for tr in trs:
                items.append(ItemStack.parse_html(tr))

        return cls(
            owner=owner.text_content(),
            items=items,
        )

    def __iter__(self) -> Iterator[ItemStack]:  # type: ignore[override]
        yield from self.items


class ExtraDataV1(BaseModel):
    version: Literal[1] = 1
    discord_id: int | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


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
    hover_image: OptionalHttpUrl = Field(alias='field_23')
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
