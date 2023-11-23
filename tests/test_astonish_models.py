import lxml.html

from celebi.astonish.models import MemberCard, PersonalComputer

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
