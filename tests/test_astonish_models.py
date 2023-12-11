import lxml.html

from celebi.astonish.models import MemberCard, PersonalComputer
from celebi.astonish.shop import AstonishShop, PokemonType, Rarity, Region

from . import DATA_DIRECTORY


class TestMemberCard:
    def test_parse_html(self):
        with open(
            DATA_DIRECTORY / 'member_card.html',
            'rt',
            encoding='utf-8',
        ) as f:
            element = lxml.html.fragment_fromstring(f.read())

        card = MemberCard.parse_html(element)

        assert card.id == 178
        assert card.username == 'Aisling Rí Darach'
        assert card.flavour_text == (
            'Do not come for the people I love, '
            "'cause then I get scary, then I get ugly"
        )
        assert card.group == 'validating'
        assert card.age == '20'
        assert card.gender_and_pronouns == 'She/Her'
        assert card.occupation == 'Ranger'
        assert card.face_claim == ''
        assert card.blood == 'Mortal'
        assert card.inamorata == 'No'

    def test_parse_all_members(self):
        with open(
            DATA_DIRECTORY / 'members.html',
            'rt',
            encoding='utf-8',
        ) as f:
            doc = lxml.html.document_fromstring(f.read())

        for div in doc.cssselect('.member-list-member'):
            _ = MemberCard.parse_html(div)


class TestPersonalComputer:
    def test_parse_html(self):
        with open(
            DATA_DIRECTORY / 'profile_aphidoidea.html',
            'rt',
            encoding='utf-8',
        ) as f:
            doc = lxml.html.document_fromstring(f.read())

        pc = PersonalComputer.parse_html(doc)
        assert len(pc) == 9

        assert pc[0].id == 7
        assert pc[0].name == 'Squirtle'
        assert not pc[0].shiny
        assert str(pc[0].custom_sprite_url) == 'https://files.jcink.net/uploads2/astonish/variants/normal/7a.png'  # fmt: skip

        assert pc[1].id == 940
        assert pc[1].name == 'Wattrel'
        assert pc[1].shiny

        assert pc[2].id == 121
        assert pc[2].name == 'Starmie'
        assert not pc[2].shiny

        assert pc[3].id == 437
        assert pc[3].name == 'Bronzong'
        assert not pc[3].shiny

        assert pc[4].id == 726
        assert pc[4].name == 'Torracat'
        assert not pc[4].shiny

        assert pc[5].id == 957
        assert pc[5].name == 'Tinkatink'
        assert pc[5].shiny

        assert pc[6].id == 405
        assert pc[6].name == 'Luxray'
        assert not pc[6].shiny

        assert pc[7].id == 133
        assert pc[7].name == 'Eevee'
        assert not pc[7].shiny

        assert pc[8].id == 726
        assert pc[8].name == 'Torracat'
        assert pc[8].shiny

        _ = pc.model_dump_html()


class TestShop:
    def test_parse_html(self):
        with open(
            DATA_DIRECTORY / 'shop.html',
            'rt',
            encoding='utf-8',
        ) as f:
            doc = lxml.html.document_fromstring(f.read())

        shop = AstonishShop.parse_html(doc)

        _ = hash(shop)  # Check that it's hashable

        assert len(shop.regions) == 4

        assert shop.regions[0].name == 'Lythra'
        assert shop.regions[0].types == {
            PokemonType(name='normal', rarity=Rarity.COMMON),
            PokemonType(name='grass', rarity=Rarity.COMMON),
            PokemonType(name='bug', rarity=Rarity.COMMON),
            PokemonType(name='electric', rarity=Rarity.COMMON),
            PokemonType(name='poison', rarity=Rarity.COMMON),
            PokemonType(name='ghost', rarity=Rarity.RARE),
            PokemonType(name='dark', rarity=Rarity.RARE),
            PokemonType(name='water', rarity=Rarity.RARE),
            PokemonType(name='psychic', rarity=Rarity.RARE),
        }

        assert shop.regions[1].name == 'Callitris'
        assert shop.regions[1].types == {
            PokemonType(name='normal', rarity=Rarity.COMMON),
            PokemonType(name='ice', rarity=Rarity.COMMON),
            PokemonType(name='ghost', rarity=Rarity.COMMON),
            PokemonType(name='steel', rarity=Rarity.COMMON),
            PokemonType(name='water', rarity=Rarity.RARE),
            PokemonType(name='grass', rarity=Rarity.RARE),
            PokemonType(name='dark', rarity=Rarity.RARE),
            PokemonType(name='psychic', rarity=Rarity.RARE),
        }

        assert shop.regions[2].name == 'Parrya'
        assert shop.regions[2].types == {
            PokemonType(name='normal', rarity=Rarity.COMMON),
            PokemonType(name='fire', rarity=Rarity.COMMON),
            PokemonType(name='fighting', rarity=Rarity.COMMON),
            PokemonType(name='rock', rarity=Rarity.COMMON),
            PokemonType(name='dark', rarity=Rarity.COMMON),
            PokemonType(name='ground', rarity=Rarity.RARE),
            PokemonType(name='flying', rarity=Rarity.RARE),
            PokemonType(name='ghost', rarity=Rarity.RARE),
            PokemonType(name='electric', rarity=Rarity.RARE),
        }

        assert shop.regions[3].name == 'Ilex'
        assert shop.regions[3].types == {
            PokemonType(name='normal', rarity=Rarity.COMMON),
            PokemonType(name='water', rarity=Rarity.COMMON),
            PokemonType(name='flying', rarity=Rarity.COMMON),
            PokemonType(name='ground', rarity=Rarity.COMMON),
            PokemonType(name='bug', rarity=Rarity.COMMON),
            PokemonType(name='fire', rarity=Rarity.RARE),
            PokemonType(name='steel', rarity=Rarity.RARE),
            PokemonType(name='grass', rarity=Rarity.RARE),
            PokemonType(name='psychic', rarity=Rarity.RARE),
        }

        assert shop.baby_pokemon == {
            'pichu',
            'tyrogue',
            'smoochum',
            'elekid',
            'magby',
            'wyanut',
            'budew',
            'chinglin',
            'bonsly',
            'happiny',
            'munchlax',
            'riolu',
            'toxel',
        }

        assert shop.stage_1_starters == {
            'bulbasaur',
            'charmander',
            'squirtle',
            'chikorita',
            'cyndaquil',
            'totodile',
            'treecko',
            'torchic',
            'mudkip',
            'turtwig',
            'chimchar',
            'piplup',
            'snivy',
            'tepig',
            'oshawott',
            'chespin',
            'fennekin',
            'froakie',
            'rowlet',
            'litten',
            'popplio',
            'grookey',
            'scorbunny',
            'sobble',
            'sprigatito',
            'fuecoco',
            'quaxly',
        }

        assert shop.stage_2_starters == {
            'ivysaur',
            'charmeleon',
            'wartortle',
            'bayleef',
            'quilava',
            'croconaw',
            'grovyle',
            'combusken',
            'marshtomp',
            'grotle',
            'monferno',
            'prinplup',
            'servine',
            'pignite',
            'dewott',
            'quilladin',
            'braixen',
            'frogadier',
            'dartrix',
            'torracat',
            'brionne',
            'thwackey',
            'raboot',
            'drizzile',
            'floragato',
            'crocalor',
            'quaxwell',
        }

        assert shop.stage_3_starters == {
            'venusaur',
            'charizard',
            'blastoise',
            'meganium',
            'typhlosion',
            'feraligatr',
            'sceptile',
            'blaziken',
            'swampert',
            'torterra',
            'infernape',
            'empoleon',
            'serperior',
            'emboar',
            'samurott',
            'chesnaught',
            'delphox',
            'greninja',
            'decidueye',
            'incineroar',
            'rillaboom',
            'cinderace',
            'inteleon',
            'meowscarada',
            'skeledirge',
            'quaquaval',
        }

    def test_pokemon_type_is_hashable(self):
        _ = hash(PokemonType(name='test'))

    def test_region_is_hashable(self):
        _ = hash(
            Region(
                name='test',
                types=frozenset({PokemonType(name='test')}),
            )
        )
