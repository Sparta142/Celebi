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

from celebi.astonish.models import (
    Character,
    ElementNotFoundError,
    Inventory,
    MemberCard,
)
from celebi.astonish.shop import AstonishShop

if TYPE_CHECKING:
    from aiohttp.typedefs import StrOrURL
    from backoff.types import Details

__all__ = ['AstonishClient']

logger = logging.getLogger(__name__)


class LoginFailedError(Exception):
    """Indicates a failure to successfully login to the forum."""


class _ModCPFields(NamedTuple):
    form_fields: dict[str, Any]
    synthetic_fields: dict[str, Any]


class AstonishClient:
    """Incomplete wrapper around managing the ASTONISH Jcink forum."""

    base_url = URL('https://astonish.jcink.net')

    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password

        self.character_cache: TTLCache[int, Character] = TTLCache(
            maxsize=256,
            ttl=5 * 60,  # 5 minutes
        )

        # Initialized in __aenter__ where we have a running event loop
        self.session: aiohttp.ClientSession

    async def __aenter__(self) -> Self:
        self.session = aiohttp.ClientSession(self.base_url)

        # Login to the forum
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

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def close(self) -> None:
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

    async def get_shop_data(self) -> AstonishShop:
        doc = await self.get(
            login=False,
            params={
                'act': 'store',
                'code': 'shop',
                'category': 5,
            },
        )
        return AstonishShop.parse_html(doc)

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
    def _parse_modcp_fields(cls, doc: lxml.html.HtmlElement, /) -> _ModCPFields:
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
