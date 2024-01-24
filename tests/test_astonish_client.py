import lxml.html
import pytest

from celebi.astonish.client import AstonishClient

from . import DATA_DIRECTORY


def test_parse_modcp_fields():
    doc = _read_document('modcp_bryn_vaughn.html')
    form, synthetic = AstonishClient._parse_modcp_fields(doc)

    # "Synthetic" fields (not from form inputs, but from other page data)
    assert synthetic['username'] == 'Bryn Vaughn'
    assert synthetic['id'] == 45

    # Real form fields
    assert form['avatar'] == '0'
    assert form['photo'] == '0'
    assert form['title'] == ''
    assert form['website'] == 'http://'
    assert form['location'] == ''
    assert form['interests'] == ''
    assert form['signature'] == ''
    assert form['field_1'] == 'Bryn Vaughn'
    assert form['field_2'] == 'n/a'
    assert form['field_3'] == '31'
    assert form['field_4'] == '5/11'
    assert form['field_5'] == 'he/him'
    assert form['field_6'] == 'he'
    assert form['field_7'] == 'n'
    assert form['field_8'] == 'Bisexual'
    assert form['field_9'] == 'Single'
    assert form['field_10'] == '6\'0"'
    assert form['field_11'] == 'Aura Scientist'
    assert form['field_12'] == 'Pyrinas, Lythra'
    assert form['field_13'] == 'GRANBLUE FANTASY, aglovale'
    assert form['field_14'] == ''
    assert form['field_15'] == 'the lights stretch out their form while the dim continue to fade on'  # fmt: skip
    # TODO: field_16
    assert form['field_17'] == 'https://astonish.jcink.net/index.php?showtopic=55'  # fmt: skip
    assert form['field_18'] == 'habs'
    assert form['field_19'] == 'she/her'
    assert form['field_20'] == '-6'
    assert form['field_21'] == 'tdm'
    assert form['field_22'] == 'y'
    assert form['field_23'] == 'https://i.postimg.cc/j29rFPTh/agg17.png'
    assert form['field_24'] == 'n/a'
    assert len(form['field_25']) == 660
    assert form['field_26'] == ''
    assert form['field_27'] == 'a'
    assert form['field_28'] == 'ins'
    assert form['field_29'] == 'n'
    assert form['field_30'] == 'n'
    assert form['field_31'] == 'https://astonish.jcink.net/index.php?showforum=82'  # fmt: skip
    assert form['field_32'] == ''


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
    doc = _read_document(filename)
    assert AstonishClient._is_logged_in(doc)


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
    doc = _read_document(filename)
    assert AstonishClient._parse_character_group(doc) == group


def _read_document(filename: str) -> lxml.html.HtmlElement:
    with open(DATA_DIRECTORY / filename, 'rb') as f:
        return lxml.html.document_fromstring(f.read())
