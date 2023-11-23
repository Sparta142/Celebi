from abc import ABC, abstractmethod
from typing import final

import discord

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
    ):
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
    async def _first(self, interaction: discord.Interaction, button):
        await self._update(interaction, 0)

    @final
    @discord.ui.button(
        emoji='\N{BLACK LEFT-POINTING TRIANGLE}',
        disabled=True,
    )
    async def _previous(self, interaction: discord.Interaction, button):
        await self._update(interaction, self.index - 1)

    @final
    @discord.ui.button(emoji='\N{BLACK RIGHT-POINTING TRIANGLE}')
    async def _next(self, interaction: discord.Interaction, button):
        await self._update(interaction, self.index + 1)

    @final
    @discord.ui.button(emoji='\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE}')
    async def _last(self, interaction: discord.Interaction, button):
        await self._update(interaction, self.count - 1)

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
