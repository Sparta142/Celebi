from typing import TYPE_CHECKING, TypeVar

from bs4 import Tag
from lxml.html import FieldsDict, FormElement, HtmlElement, soupparser

if TYPE_CHECKING:
    from _typeshed import SupportsAllComparisons

TComparable = TypeVar('TComparable', bound='SupportsAllComparisons')


def parse_form(tree: Tag | HtmlElement) -> FieldsDict:
    if isinstance(tree, Tag):
        form = FormElement(soupparser.convert_tree(tree)[0])  # type: ignore[arg-type]
    elif isinstance(tree, HtmlElement):
        form = FormElement(tree)
    else:
        raise TypeError(f'Invalid type: {type(tree).__name__!r}')

    return form.fields


def isexception(
    exc: BaseException,
    exc_type: type[Exception] | tuple[type[Exception], ...],
) -> bool:
    if isinstance(exc, ExceptionGroup):
        return exc.subgroup(exc_type) is not None

    return not isinstance(exc, exc_type)


def clamp(
    x: TComparable,
    lower: TComparable,
    upper: TComparable,
) -> TComparable:
    if x < lower:
        return lower
    elif x > upper:
        return upper

    return x
