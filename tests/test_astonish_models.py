from pathlib import Path

from celebi.astonish.models import Pokemon

_DIRECTORY = Path(__file__).parent


class TestPokemon:
    BASE_SPRITE_URL = 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/'

    def test_parse_pc1(self):
        with open(_DIRECTORY / 'pc1.html', 'rt') as f:
            pokemon = Pokemon.parse_html(f.read())

        assert len(pokemon) == 9

        assert pokemon[0].id == 209
        assert pokemon[0].shiny
        assert pokemon[0].name == 'Snubbull'
        assert pokemon[0].sprite_url == self.BASE_SPRITE_URL + 'shiny/209.png'

        assert pokemon[1].id == 940
        assert pokemon[1].shiny
        assert pokemon[1].name == 'Wattrel'
        assert pokemon[1].sprite_url == self.BASE_SPRITE_URL + 'shiny/940.png'

        assert pokemon[2].id == 121
        assert not pokemon[2].shiny
        assert pokemon[2].name == 'Starmie'
        assert pokemon[2].sprite_url == self.BASE_SPRITE_URL + '121.png'

        assert pokemon[3].id == 437
        assert not pokemon[3].shiny
        assert pokemon[3].name == 'Bronzong'
        assert pokemon[3].sprite_url == self.BASE_SPRITE_URL + '437.png'

        assert pokemon[4].id == 726
        assert not pokemon[4].shiny
        assert pokemon[4].name == 'Torracat'
        assert pokemon[4].sprite_url == self.BASE_SPRITE_URL + '726.png'

        assert pokemon[5].id == 957
        assert pokemon[5].shiny
        assert pokemon[5].name == 'Tinkatink'
        assert pokemon[5].sprite_url == self.BASE_SPRITE_URL + 'shiny/957.png'

        assert pokemon[6].id == 405
        assert not pokemon[6].shiny
        assert pokemon[6].name == 'Luxray'
        assert pokemon[6].sprite_url == self.BASE_SPRITE_URL + '405.png'

        assert pokemon[7].id == 133
        assert not pokemon[7].shiny
        assert pokemon[7].name == 'Eevee'
        assert pokemon[7].sprite_url == self.BASE_SPRITE_URL + '133.png'

        assert pokemon[8].id == 726
        assert pokemon[8].shiny
        assert pokemon[8].name == 'Torracat'
        assert pokemon[8].sprite_url == self.BASE_SPRITE_URL + 'shiny/726.png'

    def test_parse_pc2(self):
        with open(_DIRECTORY / 'pc2.html', 'rt') as f:
            pokemon = Pokemon.parse_html(f.read())

        assert len(pokemon) == 4

        assert pokemon[0].id == 285
        assert not pokemon[0].shiny
        assert pokemon[0].name == 'Shroomish'
        assert pokemon[0].sprite_url == self.BASE_SPRITE_URL + '285.png'

        assert pokemon[1].id == 561
        assert not pokemon[1].shiny
        assert pokemon[1].name == 'Sigilyph'
        assert pokemon[1].sprite_url == self.BASE_SPRITE_URL + '561.png'

        assert pokemon[2].id == 211
        assert not pokemon[2].shiny
        assert pokemon[2].name == 'Qwilfish'
        assert pokemon[2].sprite_url == self.BASE_SPRITE_URL + '211.png'

        assert pokemon[3].id == 147
        assert not pokemon[3].shiny
        assert pokemon[3].name == 'Dratini'
        assert pokemon[3].sprite_url == self.BASE_SPRITE_URL + '147.png'

    def test_parse_empty(self):
        pokemon = Pokemon.parse_html('')
        assert pokemon == []
