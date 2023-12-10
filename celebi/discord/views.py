from abc import ABC, abstractmethod
from typing import final

import discord
from discord.enums import ButtonStyle

from celebi.utils import clamp

__all__ = ['EmbedMenu']


class EmbedMenu(ABC, discord.ui.View):
    """
    A view that creates a paginated sequence of :class:`discord.Embed`
    that may be navigated by a user through the use of component buttons.
    """

    def __init__(
        self,
        original_user: discord.User | discord.Member,
        count: int,
        *,
        timeout: float | None = 180,
    ) -> None:
        super().__init__(timeout=timeout)

        self.original_user = original_user
        self.count = count
        self.index = 0

        self._embed_cache: dict[int, discord.Embed] = {}

        # If there's only one item, there's no next/last
        if self.count == 1:
            self._next.disabled = True
            self._last.disabled = True

    @property
    def at_first(self) -> bool:
        return self.index == 0

    @property
    def at_last(self) -> bool:
        return self.index == (self.count - 1)

    @final
    @discord.ui.button(
        emoji='\N{BLACK LEFT-POINTING DOUBLE TRIANGLE}',
        disabled=True,
    )
    async def _first(self, interaction: discord.Interaction, button) -> None:
        await self._update(interaction, 0)

    @final
    @discord.ui.button(
        emoji='\N{BLACK LEFT-POINTING TRIANGLE}',
        disabled=True,
    )
    async def _previous(self, interaction: discord.Interaction, button) -> None:
        await self._update(interaction, self.index - 1)

    @final
    @discord.ui.button(emoji='\N{BLACK RIGHT-POINTING TRIANGLE}')
    async def _next(self, interaction: discord.Interaction, button) -> None:
        await self._update(interaction, self.index + 1)

    @final
    @discord.ui.button(emoji='\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE}')
    async def _last(self, interaction: discord.Interaction, button) -> None:
        await self._update(interaction, self.count - 1)

    @final
    async def default_embed(self) -> discord.Embed:
        return await self.get_embed(0)

    @final
    async def get_embed(self, index: int, /) -> discord.Embed:
        """
        Get the cached :class:`discord.Embed` for the given item index,
        creating and caching a new one if necessary.

        :param index: The index of the item to embed.
        :return: The cached embed.
        """
        try:
            return self._embed_cache[index]
        except KeyError:
            self._embed_cache[index] = await self.create_embed(index)

        return self._embed_cache[index]

    @abstractmethod
    async def create_embed(self, index: int, /) -> discord.Embed:
        """
        Create a new :class:`discord.Embed` for the given item index.

        This method must be overridden in subclasses.

        :param index: The index of the item to embed.
        :return: The new embed.
        """
        raise NotImplementedError

    @final
    async def _update(
        self,
        interaction: discord.Interaction,
        index: int,
    ) -> None:
        # Promise Discord we'll handle the interaction somehow
        await interaction.response.defer(ephemeral=True, thinking=False)

        # If we're being interacted with by a user different from the
        # original user, send an error message to that new user instead.
        if interaction.user != self.original_user:
            await interaction.followup.send(
                'Sorry! As the original user of the command, only '
                f'{self.original_user.mention} can interact with that menu.',
                ephemeral=True,
            )
            return

        # Update the view only if the current position changed
        if self._set_index(index):
            # Update our buttons to match the new position
            self._first.disabled = self.at_first
            self._previous.disabled = self.at_first
            self._next.disabled = self.at_last
            self._last.disabled = self.at_last

            # Update the message's embed and buttons
            embed = await self.get_embed(index)
            await interaction.edit_original_response(embed=embed, view=self)

    @final
    def _set_index(self, value: int, /) -> bool:
        old_index = self.index
        self.index = clamp(value, 0, self.count - 1)
        return self.index != old_index


class ConfirmationView(discord.ui.View):
    def __init__(
        self,
        original_interaction: discord.Interaction,
        *,
        timeout: float | None = 180,
    ) -> None:
        super().__init__(timeout=timeout)
        self.original_interaction = original_interaction

        self._value: bool | None = None
        self._interaction: discord.Interaction | None = None

    @classmethod
    async def display(
        cls,
        original_interaction: discord.Interaction,
        *args,
        timeout: float | None = 180,
        **kwargs,
    ) -> discord.Interaction | None:
        """
        Send a confirmation view as a response or followup to an app command.

        If the user accepts, the returned :class:`discord.Interaction`
        may be used to respond to the acceptance.
        If the user cancels, or does not respond to the view in time,
        `None` will be returned and the transaction is finished.

        In either case, the original message containing the confirmation
        view will be deleted.

        :param original_interaction: The interaction to respond to.
        :param timeout: How many seconds before the confirmation times out.
        :return: An interaction that may be responded to, or `None`.
        """
        if 'view' in kwargs:
            raise ValueError('view must not be provided')

        # Ensure the view is ephemeral unless otherwise requested
        kwargs.setdefault('ephemeral', True)

        view = kwargs['view'] = cls(original_interaction, timeout=timeout)

        # Send the followup if necessary, otherwise the initial response
        if original_interaction.response.is_done():
            await original_interaction.followup.send(*args, **kwargs)
        else:
            await original_interaction.response.send_message(*args, **kwargs)

        return await view.wait_for_result()

    @discord.ui.button(label='Cancel', style=ButtonStyle.danger)
    async def _on_cancel(
        self,
        interaction: discord.Interaction,
        button,
    ) -> None:
        await self._finish(False, interaction)

    @discord.ui.button(label='Accept', style=ButtonStyle.success)
    async def _on_accept(
        self,
        interaction: discord.Interaction,
        button,
    ) -> None:
        await self._finish(True, interaction)

    async def on_timeout(self) -> None:
        await self._finish(False, None)

    async def _finish(
        self,
        value: bool,
        interaction: discord.Interaction | None,
    ) -> None:
        self._value = value
        self._interaction = interaction
        await self.original_interaction.delete_original_response()
        self.stop()

    async def wait_for_result(self) -> discord.Interaction | None:
        await self.wait()

        if self._value:
            assert self._interaction is not None
            return self._interaction

        return None
