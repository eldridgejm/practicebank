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


class Config(typing.NamedTuple):
    """A configuration for a :class:`PracticeBank`."""

    description: str
    tagsets: typing.Mapping[str, TagSet]


class PracticeBank(typing.NamedTuple):
    config: Config
    problems: typing.Sequence[Problem]
    root: pathlib.Path
    invalid_problems: typing.Optional[typing.Sequence[exceptions.ProblemError]] = None
