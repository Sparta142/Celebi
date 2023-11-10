from celebi.utils import pokemon


class TestHeight:
    def test_less_than_1_foot(self):
        assert pokemon.height(0.1) == '0\'04" (0.1 m)'  # Cutiefly

    def test_1_foot(self):
        assert pokemon.height(0.3) == '1\'00" (0.3 m)'  # Rattata

    def test_exactly_1_meter(self):
        assert pokemon.height(1.0) == '3\'03" (1.0 m)'

    def test_tall(self):
        assert pokemon.height(8.8) == '28\'10" (8.8 m)'  # Onix


class TestWeight:
    def test_less_than_1_kilogram(self):
        assert pokemon.weight(0.2) == '0.4 lbs. (0.2 kg)'  # Cutiefly

    def test_exactly_1_kilogram(self):
        assert pokemon.weight(1.0) == '2.2 lbs. (1.0 kg)'

    def test_exactly_1_pound(self):
        assert pokemon.weight(1 / 2.20462262) == '1.0 lb. (0.5 kg)'

    def test_lightweight(self):
        assert pokemon.weight(3.5) == '7.7 lbs. (3.5 kg)'  # Rattata

    def test_heavy(self):
        assert pokemon.weight(210.0) == '463.0 lbs. (210.0 kg)'  # Onix


class TestDisplayName:
    def test_gendered_male(self):
        assert pokemon.display_name('Nidoran♂', False) == 'Nidoran M'

    def test_gendered_female(self):
        assert pokemon.display_name('Nidoran♀', False) == 'Nidoran F'

    def test_gendered_male_shiny(self):
        assert pokemon.display_name('Nidoran♂', True) == 'Nidoran M (Shiny)'

    def test_gendered_female_shiny(self):
        assert pokemon.display_name('Nidoran♀', True) == 'Nidoran F (Shiny)'

    def test_ungendered_pokemon(self):
        assert pokemon.display_name('Pikachu', False) == 'Pikachu'

    def test_ungendered_pokemon_shiny(self):
        assert pokemon.display_name('Pikachu', True) == 'Pikachu (Shiny)'
