from functools import cached_property
from typing import Self

import backoff
import mechanize
from backoff.types import Details
from mechanize._mechanize import FormNotFoundError
from mechanize._response import seek_wrapper
from yarl import URL

from celebi.astonish.models import Member


class AstonishClient:
    """
    Incomplete wrapper around moderation functions for
    Jcink Forum Hosting communities.
    """

    base_url = URL('https://astonish.jcink.net')

    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password
        self.browser = mechanize.Browser()

    @cached_property
    def index_url(self) -> URL:
        """The URL of the index page."""
        return self.base_url.with_path('index.php')

    @cached_property
    def login_url(self) -> URL:
        """The URL of the login form page."""
        return self.index_url.with_query(act='Login')

    def __enter__(self) -> Self:
        self.login()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.browser.close()

    def login(self, *, remember_me: bool = True, privacy: bool = True) -> None:
        """
        Authenticate with the forum.

        :param remember_me: Whether to log in with a long-lasting session
        :param privacy: Whether to be shown in the "online members" list
        """

        # Open the virtual browser to the login page
        self.browser.open(str(self.login_url))

        # "Focus" the login form
        self.browser.select_form(name='LOGIN', method='post')
        assert isinstance(self.browser.form, mechanize.HTMLForm)

        # Fill in the login details
        self.browser.form['UserName'] = self.username
        self.browser.form['PassWord'] = self.password
        self.browser.form['CookieDate'] = ['1'] if remember_me else ['0']
        self.browser.form['Privacy'] = ['1'] if privacy else []

        # Perform the login (storing the session cookie automatically)
        result = self.browser.submit()
        if isinstance(result, seek_wrapper):
            result.close()

    @staticmethod
    def handle_form_not_found(details: 'Details'):
        inst: AstonishClient = details['args'][0]
        inst.login()

    @backoff.on_exception(
        backoff.constant,
        (mechanize.FormNotFoundError, FormNotFoundError),
        interval=0,
        max_tries=2,
        on_backoff=handle_form_not_found,
    )
    def member_details(self, memberid: int) -> Member:
        url = self.edit_user_url(memberid)
        self.browser.open(str(url))

        self.browser.select_form(name='ibform', method='post')
        assert isinstance(self.browser.form, mechanize.HTMLForm)
        self.browser.form.set_all_readonly(True)  # For safety

        data = dict(self.browser.form._pairs())
        return Member.model_validate({'id': memberid, **data})

    def edit_user_url(self, memberid: int) -> URL:
        return self.index_url.with_query(
            act='modcp',
            f=0,
            CODE='doedituser',
            memberid=memberid,
        )
