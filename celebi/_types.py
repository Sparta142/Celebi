from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, TypeVar

if TYPE_CHECKING:
    from _typeshed import SupportsRead
    from aiopoke import Language
    from aiopoke.utils import MinimalResource


class _HasFullLanguage(Protocol):
    language: Language


class _HasMinimalLanguage(Protocol):
    language: 'MinimalResource[Language]'


HasLanguage = _HasFullLanguage | _HasMinimalLanguage
TTranslated = TypeVar('TTranslated', bound=HasLanguage)

Soupable = str | bytes | SupportsRead[str] | SupportsRead[bytes]
