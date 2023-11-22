import lxml.html

from celebi.astonish.models import MemberCard

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
