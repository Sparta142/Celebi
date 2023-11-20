import pytest

from celebi.astonish.client import AstonishClient

from . import DATA_DIRECTORY


def test_parse_modcp_fields():
    with open(DATA_DIRECTORY / 'modcp_bryn_vaughn.html', 'rb') as f:
        data = AstonishClient._parse_modcp_fields(f)

    # "Synthetic" fields (not from form inputs, but from other page data)
    assert data['username'] == 'Bryn Vaughn'
    assert data['id'] == 45

    # Real form fields
    assert data['avatar'] == '0'
    assert data['photo'] == '0'
    assert data['title'] == ''
    assert data['website'] == 'http://'
    assert data['location'] == ''
    assert data['interests'] == ''
    assert data['signature'] == ''
    assert data['field_1'] == 'Bryn Vaughn'
    assert data['field_2'] == 'n/a'
    assert data['field_3'] == '31'
    assert data['field_4'] == '5/11'
    assert data['field_5'] == 'he/him'
    assert data['field_6'] == 'he'
    assert data['field_7'] == 'n'
    assert data['field_8'] == 'Bisexual'
    assert data['field_9'] == 'Single'
    assert data['field_10'] == '6\'0"'
    assert data['field_11'] == 'Aura Scientist'
    assert data['field_12'] == 'Pyrinas, Lythra'
    assert data['field_13'] == 'GRANBLUE FANTASY, aglovale'
    assert data['field_14'] == ''
    assert data['field_15'] == 'the lights stretch out their form while the dim continue to fade on'  # fmt: skip
    # TODO: field_16
    assert data['field_17'] == 'https://astonish.jcink.net/index.php?showtopic=55'  # fmt: skip
    assert data['field_18'] == 'habs'
    assert data['field_19'] == 'she/her'
    assert data['field_20'] == '-6'
    assert data['field_21'] == 'tdm'
    assert data['field_22'] == 'y'
    assert data['field_23'] == 'https://i.postimg.cc/j29rFPTh/agg17.png'
    assert data['field_24'] == 'n/a'
    assert len(data['field_25']) == 660
    assert data['field_26'] == ''
    assert data['field_27'] == 'a'
    assert data['field_28'] == 'ins'
    assert data['field_29'] == 'n'
    assert data['field_30'] == 'n'
    assert data['field_31'] == 'https://astonish.jcink.net/index.php?showforum=82'  # fmt: skip
    assert data['field_32'] == ''


@pytest.mark.parametrize(
    'filename',
    [
        'inventory_empty.html',
        'inventory_few.html',
        'inventory_many.html',
        'inventory_single.html',
        'modcp_bryn_vaughn.html',
        'profile_admin.html',
        'profile_aphidoidea.html',
        'profile_krisigos.html',
        'profile_mnemntia.html',
        'profile_mod.html',
        'profile_sophist.html',
        'profile_thiarchos.html',
    ],
)
def test_is_logged_in(filename: str):
    with open(DATA_DIRECTORY / filename, 'rb') as f:
        assert AstonishClient._is_logged_in(f)


@pytest.mark.parametrize(
    ('filename', 'group'),
    [
        ('profile_admin.html', 'Admin'),
        ('profile_aphidoidea.html', 'aphidoidea'),
        ('profile_krisigos.html', 'krisigos'),
        ('profile_mnemntia.html', 'mnemntia'),
        ('profile_mod.html', 'Mod'),
        ('profile_sophist.html', 'sophist'),
        ('profile_thiarchos.html', 'thiarchos'),
    ],
)
def test_parse_character_group(filename: str, group: str):
    with open(DATA_DIRECTORY / filename, 'rb') as f:
        assert AstonishClient._parse_character_group(f) == group
