# pyright: reportGeneralTypeIssues=false

import lxml.html
from frozendict import frozendict

from celebi.astonish.models import (
    Inventory,
    ItemStack,
    MemberCard,
    PersonalComputer,
)
from celebi.astonish.shop import AstonishShop, Rarity, Region, _PokemonType

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
            'normal': Rarity.COMMON,
            'grass': Rarity.COMMON,
            'bug': Rarity.COMMON,
            'electric': Rarity.COMMON,
            'poison': Rarity.COMMON,
            'ghost': Rarity.RARE,
            'dark': Rarity.RARE,
            'water': Rarity.RARE,
            'psychic': Rarity.RARE,
        }

        assert shop.regions[1].name == 'Callitris'
        assert shop.regions[1].types == {
            'normal': Rarity.COMMON,
            'ice': Rarity.COMMON,
            'ghost': Rarity.COMMON,
            'steel': Rarity.COMMON,
            'water': Rarity.RARE,
            'grass': Rarity.RARE,
            'dark': Rarity.RARE,
            'psychic': Rarity.RARE,
        }

        assert shop.regions[2].name == 'Parrya'
        assert shop.regions[2].types == {
            'normal': Rarity.COMMON,
            'fire': Rarity.COMMON,
            'fighting': Rarity.COMMON,
            'rock': Rarity.COMMON,
            'dark': Rarity.COMMON,
            'ground': Rarity.RARE,
            'flying': Rarity.RARE,
            'ghost': Rarity.RARE,
            'electric': Rarity.RARE,
        }

        assert shop.regions[3].name == 'Ilex'
        assert shop.regions[3].types == {
            'normal': Rarity.COMMON,
            'water': Rarity.COMMON,
            'flying': Rarity.COMMON,
            'ground': Rarity.COMMON,
            'bug': Rarity.COMMON,
            'fire': Rarity.RARE,
            'steel': Rarity.RARE,
            'grass': Rarity.RARE,
            'psychic': Rarity.RARE,
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
        _ = hash(_PokemonType(name='test'))

    def test_region_is_hashable(self):
        _ = hash(
            Region(
                name='test',
                types=frozendict({'test': Rarity.COMMON}),
            )
        )


class TestInventory:
    def test_parse_html_inventory_empty(self):
        inventory = self._read_inventory('inventory_empty.html')

        assert inventory.owner == 'ASTONISH'
        assert not inventory.items

    def test_parse_html_inventory_few(self):
        inventory = self._read_inventory('inventory_few.html')

        assert inventory.owner == 'Abelone Athanasiou'
        assert inventory.items == [
            ItemStack(
                icon_url='https://i.postimg.cc/zf06p5tP/hime.png',
                name='Hemitheo Bloodline',
                description='Create a new Hemitheo bloodline',
                stock=1,
            ),
            ItemStack(
                icon_url='https://i.postimg.cc/mhf5hrkh/ina.png',
                name='Inamorata',
                description='Give your character Inamorata status',
                stock=1,
            ),
        ]

    def test_parse_html_inventory_many(self):
        inventory = self._read_inventory('inventory_many.html')

        assert inventory.owner == 'habs'
        assert inventory.items == [
            ItemStack(
                icon_url='https://i.postimg.cc/0y2yN5wV/callitris-baby.png',
                name='Callitris (Baby)',
                description='Lure to roll for a randomized baby Pokémon from the Callitris subregion.',
                stock=1,
            ),
            ItemStack(
                icon_url='https://i.postimg.cc/X7bLZmxZ/callitris-ev1.png',
                name='Callitris (Evolution Stage 1)',
                description='Lure to roll for a randomized first stage evolution Pokémon from the Callitris subregion.',
                stock=1,
            ),
            ItemStack(
                icon_url='https://i.postimg.cc/44SZsv1F/callitris-ev2.png',
                name='Callitris (Evolution Stage 2)',
                description='Lure to roll for a randomized second stage evolution Pokémon from the Callitris subregion.',
                stock=1,
            ),
            ItemStack(
                icon_url='https://i.postimg.cc/5NQJ0H79/callitris-ev3.png',
                name='Callitris (Evolution Stage 3)',
                description='Lure to roll for a randomized third stage evolution Pokémon from the Callitris subregion.',
                stock=1,
            ),
            ItemStack(
                icon_url='https://i.postimg.cc/zXhmNsvV/callitris-s-ev1.png',
                name='Callitris Starter-type (Evolution Stage 1)',
                description='Lure to roll for a randomized first stage evolution Starter-type Pokémon from the Callitris subregion.',
                stock=1,
            ),
            ItemStack(
                icon_url='https://i.postimg.cc/pV4NgW2w/callitris-s-ev2.png',
                name='Callitris Starter-type (Evolution Stage 2)',
                description='Lure to roll for a randomized second stage evolution Starter-type Pokémon from the Callitris subregion.',
                stock=1,
            ),
            ItemStack(
                icon_url='https://i.postimg.cc/VkPxkK04/callitris-s-ev3.png',
                name='Callitris Starter-type (Evolution Stage 3)',
                description='Lure to roll for a randomized third stage evolution Starter-type Pokémon from the Callitris subregion.',
                stock=1,
            ),
            ItemStack(
                icon_url='https://i.postimg.cc/hPKs3TpP/hemi-char.png',
                name='Hemitheo Blood',
                description='Create a new Hemitheo character',
                stock=1,
            ),
            ItemStack(
                icon_url='https://i.postimg.cc/zf06p5tP/hime.png',
                name='Hemitheo Bloodline',
                description='Create a new Hemitheo bloodline',
                stock=1,
            ),
            ItemStack(
                icon_url='https://i.postimg.cc/9fDXGx1T/ilex-baby.png',
                name='Ilex (Baby)',
                description='Lure to roll for a randomized baby Pokémon from the Ilex subregion.',
                stock=1,
            ),
            ItemStack(
                icon_url='https://i.postimg.cc/50rGdgMB/ilex-ev2.png',
                name='Ilex (Evolution Stage 2)',
                description='Lure to roll for a randomized second stage evolution Pokémon from the Illex subregion.',
                stock=1,
            ),
            ItemStack(
                icon_url='https://i.postimg.cc/QCWzX7XR/ilex-ev3.png',
                name='Ilex (Evolution Stage 3)',
                description='Lure to roll for a randomized third stage evolution Pokémon from the Illex subregion.',
                stock=1,
            ),
            ItemStack(
                icon_url='https://i.ibb.co/Q6q25VX/newilex1.png',
                name='Ilex Starter-type (Evolution Stage 1)',
                description='Lure to roll for a randomized first stage evolution Starter-type Pokémon from the Ilex subregion.',
                stock=1,
            ),
            ItemStack(
                icon_url='https://i.ibb.co/b6PpkZ3/newilex2.png',
                name='Ilex Starter-type (Evolution Stage 2)',
                description='Lure to roll for a randomized second stage evolution Starter-type Pokémon from the Ilex subregion.',
                stock=1,
            ),
            ItemStack(
                icon_url='https://i.ibb.co/zF1Nj2r/newilex3.png',
                name='Ilex Starter-type (Evolution Stage 3)',
                description='Lure to roll for a randomized third stage evolution Starter-type Pokémon from the Ilex subregion.',
                stock=1,
            ),
            ItemStack(
                icon_url='https://i.postimg.cc/mhf5hrkh/ina.png',
                name='Inamorata',
                description='Give your character Inamorata status',
                stock=1,
            ),
            ItemStack(
                icon_url='https://i.postimg.cc/Pq0XKmF7/lythra-baby.png',
                name='Lythra (Baby)',
                description='Lure to roll for a randomized baby Pokémon from the Lythra subregion.',
                stock=1,
            ),
            ItemStack(
                icon_url='https://i.postimg.cc/c1pxfM8t/lythra-ev2.png',
                name='Lythra (Evolution Stage 2)',
                description='Lure to roll for a randomized second stage evolution Pokémon from the Lythra subregion.',
                stock=1,
            ),
            ItemStack(
                icon_url='https://i.postimg.cc/Qdsjy8mX/lythra-ev3.png',
                name='Lythra (Evolution Stage 3)',
                description='Lure to roll for a randomized third stage evolution Pokémon from the Lythra subregion.',
                stock=1,
            ),
            ItemStack(
                icon_url='https://i.ibb.co/gg85S9G/newlythra1.png',
                name='Lythra Starter-type (Evolution Stage 1)',
                description='Lure to roll for a randomized first stage evolution Starter-type Pokémon from the Lythra subregion.',
                stock=1,
            ),
            ItemStack(
                icon_url='https://i.ibb.co/nkWf0RB/newlythra3.png',
                name='Lythra Starter-type (Evolution Stage 3)',
                description='Lure to roll for a randomized third stage evolution Starter-type Pokémon from the Callitris subregion.',
                stock=1,
            ),
            ItemStack(
                icon_url='https://i.ibb.co/G3f8YdX/redux.png',
                name='Nerakos Lure',
                description='Lure to roll for a randomized first stage evolution Pokémon from Nerákos.',
                stock=1,
            ),
            ItemStack(
                icon_url='https://i.postimg.cc/13Hyxk7D/parrya-ev2.png',
                name='Parrya (Evolution Stage 2)',
                description='Lure to roll for a randomized second stage evolution Pokémon from the Parrya subregion.',
                stock=1,
            ),
            ItemStack(
                icon_url='https://i.postimg.cc/6QbwqdX3/sophist-krisigos.png',
                name='Sophistry (Krisigos)',
                description='Become a Kourotrophos',
                stock=1,
            ),
            ItemStack(
                icon_url='https://i.postimg.cc/TwyxDpdc/sophist-mnemntia.png',
                name='Sophistry (Mnemntia)',
                description='Become a Professor',
                stock=1,
            ),
            ItemStack(
                icon_url='https://i.postimg.cc/fL6NjDkQ/sophist-strategos.png',
                name='Sophistry (Strategos)',
                description='Become a Hero of Gaia',
                stock=1,
            ),
            ItemStack(
                icon_url='https://i.postimg.cc/gj8PgQ6X/sophist-thiarchos.png',
                name='Sophistry (Thiarchos)',
                description='Become Gilded',
                stock=1,
            ),
        ]

    def test_parse_html_inventory_single(self):
        inventory = self._read_inventory('inventory_single.html')

        assert inventory.owner == 'Bryn Vaughn'
        assert inventory.items == [
            ItemStack(
                icon_url='https://i.postimg.cc/zf06p5tP/hime.png',
                name='Hemitheo Bloodline',
                description='Create a new Hemitheo bloodline',
                stock=1,
            )
        ]

    @staticmethod
    def _read_inventory(filename: str) -> Inventory:
        with open(DATA_DIRECTORY / filename, 'rt', encoding='utf-8') as f:
            doc = lxml.html.document_fromstring(f.read())

        return Inventory.parse_html(doc)
