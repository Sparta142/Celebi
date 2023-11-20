import asyncio
import inspect
import re
from typing import TYPE_CHECKING, Any, Self

import aiohttp
import backoff
from bs4 import BeautifulSoup, SoupStrainer, Tag
from yarl import URL

from celebi.astonish.models import (
    Character,
    ElementNotFoundError,
    Inventory,
    ItemStack,
)
from celebi.utils import parse_form

if TYPE_CHECKING:
    from aiohttp.typedefs import StrOrURL
    from backoff.types import Details

    from celebi._types import Soupable

__all__ = ['AstonishClient']


class LoginFailedError(Exception):
    """Indicates a failure to successfully login to the forum."""


class CharacterLookupError(LookupError):
    """Indicates that the requested character was not found."""


class AstonishClient:
    """Incomplete wrapper around managing the ASTONISH Jcink forum."""

    base_url = URL('https://astonish.jcink.net')

    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password

        # Initialized in __aenter__ where we have a running event loop
        self.session: aiohttp.ClientSession

    async def __aenter__(self) -> Self:
        self.session = aiohttp.ClientSession(self.base_url)
        await self.login()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def close(self) -> None:
        await self.session.close()

    async def login(self) -> None:
        """Authenticate with the forum."""

        data = {
            'referer': '',
            'UserName': self.username,
            'PassWord': self.password,
            'CookieDate': 1,  # "Remember me"
            'Privacy': 1,  # "Don't add me to the active users list"
        }

        # The client session will store the necessary session cookies
        async with self.session.post(
            '/index.php',
            params={'act': 'Login', 'CODE': '01'},
            data=data,
        ) as response:
            response.raise_for_status()

    async def get_character(self, memberid: int) -> Character:
        try:
            # Fetch the Mod CP data and profile data concurrently
            async with asyncio.TaskGroup() as tg:
                fields_task = tg.create_task(self._get_modcp_fields(memberid))
                group_task = tg.create_task(self.get_character_group(memberid))
        except* ElementNotFoundError as e:
            # This is *probably* because the character doesn't exist
            raise CharacterLookupError(memberid) from e

        fields = await fields_task
        fields['group'] = await group_task

        assert fields['id'] == memberid, 'Member ID does not match'

        return Character.model_validate(fields, from_attributes=False)

    async def get_character_group(self, memberid: int) -> str:
        markup = await self.get(params={'showuser': memberid})
        return self._parse_character_group(markup)

    async def get_inventory(self, memberid: int) -> Inventory:
        params = {
            'act': 'store',
            'code': 'view_inventory',
            'memberid': memberid,
        }

        async with self.session.get('/index.php', params=params) as response:
            response.raise_for_status()
            text = await response.text()

        soup = BeautifulSoup(text, 'lxml')

        # Get the inventory owner
        owner = soup.select_one(
            '#ucpcontent > table tr:nth-child(1) > td:nth-child(2) > a'
        )
        if not owner:
            raise ValueError('Inventory owner not found')

        # Get all items
        items: list[ItemStack] = []
        trs = soup.select('#ucpcontent > table tr')[3:]

        if trs[0].text.strip() != 'Inventory Empty.':
            for tr in trs:
                tds = tr.find_all('td', recursive=False)
                items.append(
                    ItemStack(
                        icon_url=tds[0].find('img')['src'],
                        name=tds[1].text,
                        description=tds[2].text,
                        stock=tds[3].text,
                    )
                )

        return Inventory(owner=owner.text, items=items)

    async def _get_modcp_fields(self, memberid: int) -> dict[str, Any]:
        markup = await self.get(
            login=True,
            params={
                'act': 'modcp',
                'CODE': 'doedituser',
                'memberid': memberid,
            },
        )
        return self._parse_modcp_fields(markup)

    @inspect.markcoroutinefunction  # @staticmethod is not recognized as async
    @staticmethod
    async def _handle_not_logged_in(details: 'Details') -> None:
        self: AstonishClient = details['args'][0]
        await self.login()

    @backoff.on_exception(
        backoff.constant,
        LoginFailedError,
        interval=0,  # Retry immediately
        max_tries=2,  # Retry once (the try + the retry = 2 tries)
        on_backoff=_handle_not_logged_in,
    )
    async def get(
        self,
        url: 'StrOrURL' = '/index.php',
        *,
        login: bool = True,
        **kwargs,
    ) -> str:
        if login and not self._has_session_cookies():
            await self.login()

        async with self.session.get(url, **kwargs) as response:
            response.raise_for_status()
            markup = await response.text()

        if login and not self._is_logged_in(markup):
            raise LoginFailedError('Session cookies set but not logged in')

        return markup

    def _has_session_cookies(self) -> bool:
        cookies = self.session.cookie_jar.filter_cookies(self.base_url)
        return ('session_id' in cookies) and ('pass_hash' in cookies)

    @staticmethod
    def _is_logged_in(markup: 'Soupable', /) -> bool:
        soup = BeautifulSoup(
            markup,
            'lxml',
            parse_only=SoupStrainer(['ul', 'li']),
        )

        a = soup.select_one(
            '#mobile-menu-activate > li[title="user profile"] > a[href*="showuser="]'
        )
        if not isinstance(a, Tag):
            raise ElementNotFoundError('<a href="...">')

        match a['href']:
            case [str(href), *_]:
                url = URL(href)
            case str(href):
                url = URL(href)
            case _:
                raise AssertionError()

        # If the showuser param is not 0, it (probably) refers
        # to the member ID of the currently logged-in user.
        return url.query.get('showuser') != '0'

    @classmethod
    def _parse_modcp_fields(cls, markup: 'Soupable', /) -> dict[str, Any]:
        def _match_form_action(action: str) -> bool:
            url = URL(action)
            return (
                url.origin() == cls.base_url.origin()
                and url.path == '/index.php'
                and url.query.get('act') == 'modcp'
                and url.query.get('CODE') == 'compedit'
                and 'memberid' in url.query
            )

        soup = BeautifulSoup(
            markup,
            'lxml',
            parse_only=SoupStrainer(['div', 'form']),
        )

        # Find the div containing the username
        pattern = re.compile(r'^Edit a users profile: (?P<username>.+)$', re.I)

        maintitle = soup.find('div', class_='maintitle', string=pattern)
        if not isinstance(maintitle, Tag):
            raise ElementNotFoundError('<div class="maintitle">')

        # Parse out the username with a regex (it should always match)
        match = pattern.fullmatch(maintitle.text)
        assert match is not None, "BeautifulSoup matched but re didn't"

        # Find the "Edit a users profile" form so that we can take its fields
        ibform = soup.find(
            'form',
            attrs={
                'name': 'ibform',
                'method': 'post',
                'action': _match_form_action,
            },
        )
        if not isinstance(ibform, Tag):
            raise ElementNotFoundError('<form name="ibform"...>')

        # Parse the member ID out of the form action URL
        action = URL(ibform.attrs['action'])
        memberid = int(action.query['memberid'])

        return {
            'username': match.group('username'),
            'id': memberid,
            **parse_form(ibform),
        }

    @staticmethod
    def _parse_character_group(markup: 'Soupable', /) -> str:
        soup = BeautifulSoup(
            markup,
            'lxml',
            parse_only=SoupStrainer(['li', 'span']),
        )

        span = soup.select_one('#main-profile-trainer-class > span.description')
        if not isinstance(span, Tag):
            raise ElementNotFoundError('<span class="description">')

        return span.text.strip()
