import pathlib
import typing

from . import exceptions


class Problem(typing.NamedTuple):
    """A problem."""

    contents: str
    format: str
    tags: typing.Set[str]
    identifier: str
    path: pathlib.Path
    source: typing.Optional[str] = None


class TagSet(typing.NamedTuple):
    """A set of tags."""

    identifier: str
    title: str
    description: str
    tags: typing.Union[str, typing.Set[str]]


class Badge(typing.NamedTuple):
    """A tag that is shown as a symbol next to a problem's number.

    Badge tags are not listed with a problem's other tags and get no tag page.
    Pages that list problems can be filtered to show only problems with a badge.

    """

    tag: str
    symbol: str
    title: typing.Optional[str] = None


class Config(typing.NamedTuple):
    """A configuration for a :class:`PracticeBank`."""

    description: str
    tagsets: typing.Mapping[str, TagSet]
    badges: typing.Sequence[Badge] = ()
    default_code_language: typing.Optional[str] = None


class PracticeBank(typing.NamedTuple):
    config: Config
    problems: typing.Sequence[Problem]
    root: pathlib.Path
    invalid_problems: typing.Optional[typing.Sequence[exceptions.ProblemError]] = None
