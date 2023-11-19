import pytest

from celebi.astonish.models import Profile, TrainerClass

from . import DATA_DIRECTORY


class TestProfileParseHtml:
    def test_admin(self):
        with open(DATA_DIRECTORY / 'profile_admin.html', 'rb') as f:
            profile = Profile.parse_html(f)

        assert profile.character_name == 'ASTONISH'
        assert profile.group == 'Admin'

        with pytest.raises(ValueError):
            profile.trainer_class()

    def test_aphidoidea(self):
        with open(DATA_DIRECTORY / 'profile_aphidoidea.html', 'rb') as f:
            profile = Profile.parse_html(f)

        assert profile.character_name == 'Magikarp'
        assert profile.group == 'aphidoidea'
        assert profile.trainer_class() is TrainerClass.APHIDOIDEA

    def test_krisigos(self):
        with open(DATA_DIRECTORY / 'profile_krisigos.html', 'rb') as f:
            profile = Profile.parse_html(f)

        assert profile.character_name == 'Amos Raines'
        assert profile.group == 'krisigos'
        assert profile.trainer_class() is TrainerClass.KRISIGOS

    def test_mnemntia(self):
        with open(DATA_DIRECTORY / 'profile_mnemntia.html', 'rb') as f:
            profile = Profile.parse_html(f)

        assert profile.character_name == 'Bryn Vaughn'
        assert profile.group == 'mnemntia'
        assert profile.trainer_class() is TrainerClass.MNEMNTIA

    def test_mod(self):
        with open(DATA_DIRECTORY / 'profile_mod.html', 'rb') as f:
            profile = Profile.parse_html(f)

        assert profile.character_name == 'Celebi'
        assert profile.group == 'Mod'

        with pytest.raises(ValueError):
            profile.trainer_class()

    def test_sophist(self):
        with open(DATA_DIRECTORY / 'profile_sophist.html', 'rb') as f:
            profile = Profile.parse_html(f)

        assert profile.character_name == 'Cameron Aster'
        assert profile.group == 'sophist'
        assert profile.trainer_class() is TrainerClass.SOPHIST

    def test_thiarchos(self):
        with open(DATA_DIRECTORY / 'profile_thiarchos.html', 'rb') as f:
            profile = Profile.parse_html(f)

        assert profile.character_name == 'Lyla Dumouchel'
        assert profile.group == 'thiarchos'
        assert profile.trainer_class() is TrainerClass.THIARCHOS
