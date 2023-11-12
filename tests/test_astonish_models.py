from pathlib import Path

from celebi.astonish.models import (
    BloodType,
    ContactMethod,
    MatureContent,
    Member,
    Pokemon,
    Proficiency,
)

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


class TestMember:
    def test_parse_member(self):
        member = Member.model_validate(
            {
                'id': 45,
                'avatar': '0',
                'photo': '0',
                'title': '',
                'website': 'http://',
                'location': '',
                'interests': '',
                'signature': '',
                'field_1': 'Bryn Vaughn',
                'field_2': 'n/a',
                'field_3': '31',
                'field_4': '5/11',
                'field_5': 'Cisgender male (he/him)',
                'field_6': 'he',
                'field_7': 'n',
                'field_8': 'Bisexual',
                'field_9': 'Single',
                'field_10': '6\'0"',
                'field_11': 'Aura Scientist',
                'field_12': 'Pyrinas, Lythra',
                'field_13': 'GRANBLUE FANTASY, aglovale',
                'field_14': '',
                'field_15': 'the lights stretch out their form while the dim continue to fade on',
                'field_16': "<tw>parental death, mental illness</tw>\r\n<center><h2>a white horse called conquest</h2></center>\r\n<blockquote>you're born on an unreasonably icy noem morning. those early years of your life weren't noteworthy—and any memories you might have had were erased either by time or mundanity, perhaps both. but at the tender age of seven, mere months before your eighth birthday, one memory has stuck in your brain for twenty-three years: the day your parents brought home idris.\r\n\r\nat first you were upset. you'd grown accustomed to your life as the sole vaughn child, but time has a way of easing all aches and pains, even  those held by a mere boy. once your brother learned how to walk and could babble a few words, you'd decided that he wasn't so bad after all.  in fact, you might even say that you liked him. <i>loved</i> him. your father reminded you often how important it was to be not only brothers, but friends—because someday he might be all you had left.\r\n\r\nat the time, you didn't know how true those words would someday ring.\r\n\r\nas a boy, you had no worries. how could've you, after all—you were a child, unable to understand the magnitude of your name and not even expected to in the first place. for all their failings, one thing your parents seemed to do right was to make life as simple as possible for you and your brother so you could enjoy those early years—an act of love amidst the cruel landscape your parents had chosen to navigate in this world.\r\n\r\nyou suppose, for that reason, the fact that you don't remember much is a blessing. you don't remember the strange visitors, knocking in codes and whispering with your mother through the crack between the jamb and the door. you don't remember the phone calls late into the night and how you couldn't sleep because you could feel the aura sparking into your father's aura conductor to keep his cell phone on.\r\n\r\nyou didn't know. and thus, you could not be blamed.</blockquote>\r\n\r\n<center><h2>a red horse called war</h2></center>\r\n<blockquote>you're eighteen when you find your parents dead. while some might use this phrase as a hyperbole, for you it was anything but. you think about your childhood of simplicity, devoid of recollection. you desperately wish you could remember your favorite toys or your first time seeing a pokémon or when you rode a bike without training wheels for the first time or—anything. anything else. \r\n\r\nthis new memory was one you wished could be erased with time. unfortunately, memories like that don't just go away.\r\n\r\nit's a small wonder idris wasn't with you when you opened the door, and for that you are thankful. there has to be something positive for you to focus on, to cling to, so you don't get lost in the wave of crushing emptiness that comes from seeing your mother and father lying lifeless on the floor. \r\n\r\nyou don't remember if you cried.\r\n\r\nthe next few days were a flurry of activity, and all you can remember is how sore your hand was after signing document after document. there was a will, an inheritance, an adoption form, and a dizzying stack of papers stamped with \"vaughn industries\" at the top. your father's lawyer was to your left and idris was to your right as you initialed and dated on this line, and this one, and that one, and this one.\r\n\r\nyour father's company was handed over to the COO—not <i>you</i>, nor did you ever want it to be <i>you</i>. after all, your father was no king, and you were no heir. you were eighteen, barely out of childhood before being shoved over the threshold of adulthood. the CFO mentions that while you're not ready right now, someday you could—said in a way that implied <i>should</i>—helm the company.\r\n\r\nyou reassure her that's not going to happen. you don't intend to sneer, but you can't hold back the slightest curl of your lip. if it offended her, she never let you know.\r\n\r\nafter investigating, law enforcement told you they suspected foul play. you didn't know the depths of what your parents had been doing, and to be honest, you still don't fully understand. all you know is there was a deal gone wrong and someone had gotten mad. the police seemed to think you and your brother weren't in danger because the killer had already dealt with the objects of their frustration. you wanted to remind the detective that at one point, those objects had been humans, but you didn't say it.\r\n\r\nyou couldn't get your mouth to open. \r\n\r\nin fact, you couldn't say anything for days. two constants kept you grounded: your brother, and your father's corviknight, left to you now that your father was gone. the corviknight, simply named \"cor,\" had spent most of his life in a pokéball. you let him out when you got home from the police station and never put him back in.</blockquote>\r\n\r\n<center><h2>a black horse called famine</h2></center>\r\n<blockquote>your house had never been so quiet.\r\n\r\nfor as long as you could remember, you could hear the thrumming of aura in the air as it funneled into the small conductors your parents wore around their necks. they were metic, and though they'd both lived in gaia for some time, they still weren't able to manipulate aura like you and your brother could. even now, just looking at the forgotten conductors made you cognizant of the spark of aura on your fingertips.\r\n\r\nthere was a small \"v\" etched into the side of the conductor, the logo of vaughn industries. your father's business wasn't the first to dive into the business of aura conductors, and you never really got the chance to ask him why he'd done it. there were a lot of things you'd never gotten to ask your father. but you'd learned it wasn't healthy to dwell on these thoughts, so you turned your attention back to the lifeless conductor in your hands.\r\n\r\nlong ago—in childhood, before your parents died—you had decided that going into the family business wasn't part of the plan...but then again, in recent years the plan had changed. it would change again when you decided on a whim to pry open the conductor, poking at its innards to try and figure out how it worked. you'd never truly understood conductors since you'd never needed them yourself.\r\n\r\nthe pursuit of the unknown was fascinating. and for the first time in a long time, as you dissected the aura conductor, you felt a spark of interest take hold in your brain.\r\n\r\nby your twenty-fifth birthday there are two diplomas hanging upon your wall, your name emblazoned in calligraphy alongside the words \"bachelor of science in aura science\" and \"master of science in aura conduction engineering.\" on your desk is an official job offer letter from vaughn industries. at this point, it feels more like a formality.\r\n\r\nyour own words of defiance echo in your brain as you scann the letter, a memory that has not been yet lost to time. you feel hungry for something you don't know the taste of.</blockquote>\r\n\r\n<center><h2>a pale horse called death</h2></center>\r\n<blockquote>you were not yet a father, and yet you simultaneously were. parentification, your therapist called it. she said it was likely the cause of your gnawing anxiety, your chronic headaches, and your inability to hold a relatiionship down longer than a few months. (that last part kind of stung, but deep down you knew she was right.) at least SSRIs and beta blockers could help with the first two problems.\r\n\r\nby now you'd hoped things might ease off, but idris, even in his twenties, was not in the business of making things easy for you.\r\n\r\nyou were called to the hospital at three a.m. to find idris there, waiting to be brought home. it had been a minor infraction but a <i>dangerous</i> one, leaving your brother injured and your mind reeling as you tried to pull yourself back from the edge of panic. for what would you do if death claimed the only person you had left on this earth?\r\n\r\nyou gave your brother an ultimatum: become a strategos or get cut off. in truth, it wasn't much of a threat—idris had mentioned his desire to become a strategos in the past, though he had never taken the steps to get started. but each incident that your brother found himself in inched him closer to potential disaster, and the last time had been the final time.\r\n\r\nto your surprise, idris didn't fight back. he followed up on his word and went on to start his journey as a strategos, but that's a story best <a href=\"https://astonish.jcink.net/index.php?showuser=42\">saved for another time</a>.\r\n\r\nyour thirtieth birthday is an uncommonly frigid noum day. dawn is breaking as you amble out of bed, stretching out the soreness of your pre-arthritic joints. you absentmindedly count the aura pulses on your fingertips as you scroll on your phone while walking on the treadmill at the gym before heading off to the train to ride to the vaughn r&d lab for your shift. it's the same morning you had yesterday and the same morning you'll probably have tomorrow, too.\r\n\r\nbanality is the death of excitement, or so some say, but you suppose you've had enough excitement to last you a while. mundanity will do—as it has always done—just fine.</blockquote>\r\n\r\n",
                'field_17': 'https://astonish.jcink.net/index.php?showtopic=55',
                'field_18': 'habs',
                'field_19': 'she/her',
                'field_20': '-6',
                'field_21': 'tdm',
                'field_22': 'y',
                'field_23': 'https://sig.grumpybumpers.com/host/hbrynbig.gif',
                'field_24': 'n/a',
                'field_25': '<div class="pkmn-display"><i class="fa-solid fa-sparkles"></i><div class="pkmn-name">Corviknight</div><img src="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/823.png"/></div><div class="pkmn-display"><i class="fa-solid fa-sparkles"></i><div class="pkmn-name">Nickit</div><img src="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/827.png"/></div><div class="pkmn-display"><i class="fa-solid fa-sparkles"></i><div class="pkmn-name">Glameow</div><img src="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/431.png"/></div>',
                'field_26': '',
                'field_27': 'a',
                'field_28': 'ins',
                'field_29': 'n',
                'field_30': 'n',
                'field_31': 'https://astonish.jcink.net/index.php?showforum=82',
            }
        )

        assert member.title == ''
        assert member.website == 'http://'
        assert member.location == ''
        assert member.interests == ''
        assert member.full_name == 'Bryn Vaughn'
        assert member.nicknames == 'n/a'
        assert member.age == '31'
        assert member.date_of_birth == '5/11'
        assert member.gender_and_pronouns == 'Cisgender male (he/him)'
        assert member.blood_type is BloodType.HEMITHEO
        assert member.inamorata_status is False
        assert member.orientation == 'Bisexual'
        assert member.marital_status == 'Single'
        assert member.height == '6\'0"'
        assert member.occupation == 'Aura Scientist'
        assert member.home_region == 'Pyrinas, Lythra'
        assert member.face_claim == 'GRANBLUE FANTASY, aglovale'
        assert member.art_credits == ''
        assert member.player_pronouns == 'she/her'
        assert member.player_timezone == -6
        assert member.preferred_contact_method is ContactMethod.TAGS_OR_DMS
        assert member.mature_content is MatureContent.YES
        assert member.flavour_text == 'the lights stretch out their form while the dim continue to fade on'  # fmt: skip
        assert len(member.biography) == 9041
        assert member.plot_page == 'https://astonish.jcink.net/index.php?showtopic=55'  # fmt: skip
        assert member.player_name == 'habs'
        assert member.player_pronouns == 'she/her'
        assert member.triggers_and_warnings == 'n/a'
        assert member.personal_computer == [
            Pokemon(id=823, name='Corviknight'),
            Pokemon(id=827, name='Nickit'),
            Pokemon(id=431, name='Glameow'),
        ]
        assert member.inamorata_ability == ''
        assert member.proficiency_1 is Proficiency.AURA
        assert member.proficiency_2 is Proficiency.INSIGHT
        assert member.proficiency_3 is Proficiency.NONE
        assert member.proficiency_4 is Proficiency.NONE
        assert member.development_forum == 'https://astonish.jcink.net/index.php?showforum=82'  # fmt: skip

        assert member.proficiencies == [Proficiency.AURA, Proficiency.INSIGHT]
