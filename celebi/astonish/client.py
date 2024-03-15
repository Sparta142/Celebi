from __future__ import annotations as _annotations

import asyncio
import inspect
import logging
import re
from contextlib import suppress
from typing import TYPE_CHECKING, Any, NamedTuple, Self

import aiohttp
import backoff
import lxml.html
from cachetools import TTLCache
from yarl import URL

from celebi import pokemon
from celebi.astonish.item import ItemBehavior, LureBehavior
from celebi.astonish.models import Character, Inventory, MemberCard
from celebi.astonish.shop import AstonishShopData

if TYPE_CHECKING:
    from collections.abc import Container

    from aiohttp.typedefs import StrOrURL
    from backoff.types import Details

__all__ = ['AstonishClient']

logger = logging.getLogger(__name__)


class LoginFailedError(Exception):
    """Indicates a failure to properly log in to the forum."""


class _ModCPFields(NamedTuple):
    form_fields: dict[str, Any]
    synthetic_fields: dict[str, Any]


class ElementNotFoundError(Exception):
    pass


class AstonishClient:
    """Incomplete wrapper around managing the ASTONISH Jcink forum."""

    base_url = URL('https://astonish.jcink.net')

    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password

        self.character_cache: TTLCache[int, Character] = TTLCache(
            maxsize=256,
            ttl=15 * 60,  # 15 minutes
        )

        # Initialized in __aenter__ where we have a running event loop
        self.session: aiohttp.ClientSession
        self.shop: AstonishShopData
        self.items: dict[str, ItemBehavior]

    async def __aenter__(self) -> Self:
        self.session = aiohttp.ClientSession(self.base_url)

        # Log in to the forum
        await self.login()

        logger.info('Building initial character cache...')

        # Concurrently add all characters to the cache
        for fut in asyncio.as_completed(
            self.get_character(id) for id in await self.get_all_characters()
        ):
            try:
                chara = await fut
            except BaseException:
                logger.exception('Unable to add character to cache')
            else:
                self._update_in_cache(chara)

        logger.info(
            'Character cache built: %d valid characters stored',
            len(self.character_cache),
        )

        # Fetch shop (IBstore) data
        self.shop = await self._get_shop_data()

        logger.info(
            'Shop data loaded successfully: %d regions, %d baby pokemon, '
            '%d T1 starters, %d T2 starters, %d T3 starters found',
            len(self.shop.regions),
            len(self.shop.baby_pokemon),
            len(self.shop.stage_1_starters),
            len(self.shop.stage_2_starters),
            len(self.shop.stage_3_starters),
        )

        self.poke_client = pokemon.AiopokeClient()
        await self.poke_client.__aenter__()

        self.items = await self._generate_items()
        logger.info('%d items generated from shop data', len(self.items))

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def close(self) -> None:
        await self.poke_client.close()
        await self.session.close()

    async def login(self) -> None:
        """Authenticate with the forum."""

        # The client session will store the necessary session cookies
        async with self.session.post(
            '/index.php',
            params={
                'act': 'Login',
                'CODE': '01',
            },
            data={
                'referer': '',
                'UserName': self.username,
                'PassWord': self.password,
                'CookieDate': 1,  # "Remember me"
                'Privacy': 1,  # "Don't add me to the active users list"
            },
        ) as response:
            response.raise_for_status()

            if 'member_id' not in response.cookies:
                raise LoginFailedError('Response did not set expected cookie')

    async def get_character(
        self,
        memberid: int,
        *,
        cached: bool = False,
    ) -> Character:
        """
        Get an ASTONISH character.

        :param memberid: The Jcink member ID to lookup.
        :param cached: Whether to return the cached character, if present.
        :raises ValueError: When the member ID does not exist.
        :return: The requested character.
        """
        if cached:
            with suppress(KeyError):
                return self.character_cache[memberid]

        try:
            # Fetch the Mod CP data and profile data concurrently
            async with asyncio.TaskGroup() as tg:
                fields_task = tg.create_task(self._get_modcp_fields(memberid))
                group_task = tg.create_task(self.get_character_group(memberid))
        except* ElementNotFoundError as e:
            # This is *probably* because the character doesn't exist
            raise ValueError(f'Member not found: {memberid}') from e

        form, synthetic = await fields_task
        synthetic['group'] = await group_task

        assert synthetic['id'] == memberid, 'Member ID does not match'

        chara = Character.model_validate(
            {**form, **synthetic},
            from_attributes=False,
        )
        self._update_in_cache(chara)
        return chara

    async def get_character_group(self, memberid: int) -> str:
        """
        Get the group name associated with the given member ID.

        :param memberid: The Jcink member ID to lookup
        :return: The member's group
        """
        doc = await self.get(params={'showuser': memberid})
        return self._parse_character_group(doc)

    async def get_inventory(self, memberid: int) -> Inventory:
        """
        Get a member's IBStore inventory.

        :param memberid: The Jcink member ID to lookup
        :return: The member's inventory
        """
        doc = await self.get(
            params={
                'act': 'store',
                'code': 'view_inventory',
                'memberid': memberid,
            },
        )
        return Inventory.parse_html(doc)

    async def update_character(self, character: Character) -> None:
        form, synthetic = await self._get_modcp_fields(character.id)
        form['field_25'] = character.personal_computer.model_dump_html()
        form['field_32'] = character.extra.model_dump_json()

        action: URL = synthetic['$action']
        assert action.origin() == self.base_url.origin()

        async with self.session.post(action.relative(), data=form) as response:
            response.raise_for_status()

        self._update_in_cache(character)

    async def get_all_characters(self) -> dict[int, MemberCard]:
        doc = await self.get(
            login=False,
            params={
                'act': 'Members',
                'max_results': 1000,  # The forum returns an error over 1000
            },
        )

        members: dict[int, MemberCard] = {}

        for div in doc.cssselect('div.member-list-member'):
            card = MemberCard.parse_html(div)
            members[card.id] = card

        return members

    async def _get_shop_data(self) -> AstonishShopData:
        doc = await self.get(
            login=False,
            params={
                'act': 'store',
                'code': 'shop',
                'category': 5,
            },
        )
        return AstonishShopData.parse_html(doc)

    async def _get_modcp_fields(self, memberid: int) -> _ModCPFields:
        doc = await self.get(
            login=True,
            params={
                'act': 'modcp',
                'CODE': 'doedituser',
                'memberid': memberid,
            },
        )
        return self._parse_modcp_fields(doc)

    @inspect.markcoroutinefunction  # @staticmethod is not recognized as async
    @staticmethod
    async def _on_login_failed(details: Details) -> None:
        self: AstonishClient = details['args'][0]
        await self.login()

    @backoff.on_exception(
        backoff.constant,
        LoginFailedError,
        interval=0,  # Retry immediately
        max_tries=2,  # Retry once (the try + the retry = 2 tries)
        on_backoff=_on_login_failed,
    )
    async def get(
        self,
        url: StrOrURL = '/index.php',
        *,
        login: bool = True,
        **kwargs: Any,
    ) -> lxml.html.HtmlElement:
        if login and not self._has_session_cookies():
            await self.login()

        async with self.session.get(url, **kwargs) as response:
            response.raise_for_status()
            markup = await response.text()

        doc = lxml.html.document_fromstring(markup)

        if login and not self._is_logged_in(doc):
            raise LoginFailedError('Session cookies set but not logged in')

        return doc

    def _has_session_cookies(self) -> bool:
        cookies = self.session.cookie_jar.filter_cookies(self.base_url)
        return ('session_id' in cookies) and ('pass_hash' in cookies)

    def _update_in_cache(self, chara: Character) -> None:
        self.character_cache[chara.id] = chara

    async def _generate_items(self) -> dict[str, ItemBehavior]:
        shop = self.shop
        items: dict[str, ItemBehavior] = {}

        for region in shop.regions.values():
            # Baby pokemon lure
            items[f'{region.name} (Baby)'] = LureBehavior(
                await _get_lure_pokemon(
                    self.poke_client,
                    region.types,
                    allowlist=shop.baby_pokemon,
                )
            )

            # Starter stage 1-3 lures
            items[f'{region.name} Starter-type (Evolution Stage 1)'] = (
                LureBehavior(
                    await _get_lure_pokemon(
                        self.poke_client,
                        region.types,
                        allowlist=shop.stage_1_starters,
                    )
                )
            )

            items[f'{region.name} Starter-type (Evolution Stage 2)'] = (
                LureBehavior(
                    await _get_lure_pokemon(
                        self.poke_client,
                        region.types,
                        allowlist=shop.stage_2_starters,
                    )
                )
            )

            items[f'{region.name} Starter-type (Evolution Stage 3)'] = (
                LureBehavior(
                    await _get_lure_pokemon(
                        self.poke_client,
                        region.types,
                        allowlist=shop.stage_3_starters,
                    )
                )
            )

            # Evolution stage 1-3 lures
            items[f'{region.name} (Evolution Stage 1)'] = LureBehavior(
                await _get_lure_pokemon(self.poke_client, region.types, stage=1)
            )

            items[f'{region.name} (Evolution Stage 2)'] = LureBehavior(
                await _get_lure_pokemon(self.poke_client, region.types, stage=2)
            )

            items[f'{region.name} (Evolution Stage 3)'] = LureBehavior(
                await _get_lure_pokemon(self.poke_client, region.types, stage=3)
            )

        return items

    @staticmethod
    def _is_logged_in(doc: lxml.html.HtmlElement, /) -> bool:
        (a,) = doc.cssselect(
            '#mobile-menu-activate > li[title="user profile"] > a[href*="showuser="]'
        )
        url = URL(a.attrib['href'])

        # If the showuser param is not 0, it (probably) refers
        # to the member ID of the currently logged-in user.
        return url.query.get('showuser', '0') != '0'

    @classmethod
    def _parse_modcp_fields(
        cls,
        doc: lxml.html.HtmlElement,
        /,
    ) -> _ModCPFields:
        # Find the div containing the username
        pattern = re.compile(r'^Edit a users profile: (?P<username>.+)$', re.I)

        for div in doc.cssselect('div.maintitle'):
            if match := pattern.fullmatch(div.text or ''):
                username = match.group('username')
                break
        else:
            raise ValueError('Username not found')  # We didn't break

        # Find the "Edit a users profile" form so that we can take its fields
        for form in doc.forms:
            action = URL(form.action)

            if (
                form.attrib.get('name') == 'ibform'
                and form.method.casefold() == 'post'
                and action.origin() == cls.base_url.origin()
                and action.path == '/index.php'
                and action.query.get('act') == 'modcp'
                and action.query.get('CODE') == 'compedit'
                and 'memberid' in action.query
            ):
                return _ModCPFields(
                    form_fields=dict(form.fields),
                    synthetic_fields={
                        'username': username,
                        'id': int(action.query['memberid']),
                        '$action': action,
                    },
                )

        raise ElementNotFoundError('<form name="ibform"...>')

    @staticmethod
    def _parse_character_group(doc: lxml.html.HtmlElement, /) -> str:
        (span,) = doc.cssselect(
            '#main-profile-trainer-class > span.description'
        )
        return span.text_content().strip()


async def _get_lure_pokemon(
    client: pokemon.AiopokeClient,
    types: Container[str],
    *,
    allowlist: Container[str] | None = None,
    stage: int | None = None,
):
    allowed_pkmn = []

    for res in await client.all_pokemon():
        # Skip Pokemon not on the allowlist
        if allowlist and res.name not in allowlist:
            continue

        pkmn = await res.fetch()

        # Skip special Pokemon forms
        if not pkmn.is_default:
            continue

        # Skip Pokemon who have no matching types
        if not any(t.type.name in types for t in pkmn.types):
            continue

        # Skip Pokemon who aren't at the desired stage of evolution
        if stage is not None:
            actual_stage = await client.evolution_stage(pkmn)
            if actual_stage != stage:
                continue

        allowed_pkmn.append(pkmn)

    return allowed_pkmn
