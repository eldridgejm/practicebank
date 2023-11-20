"""Load a bank of practice problems."""

import collections
import itertools
import pathlib
import typing
import yaml

import dictconfig

from .types import PracticeBank, Config, TagSet, Problem
from .exceptions import Error, ConfigError, ProblemError


# configuration file loader ============================================================

# these are the special tagsets that can be provided in lieu of a list of tags
_SPECIAL_TAGSETS = {"__ALL__"}


def _make_tagset(tagset: dict) -> TagSet:
    """Creates a :class:`TagSet` from a dictionary.

    Parameters
    ----------
    tagset : dict
        The tagset dictionary.

    Returns
    -------
    TagSet
        The resolved tagset.

    Raises
    ------
    ConfigError
        If the tagset is invalid.

    """

    schema = {
        "type": "dict",
        "required_keys": {
            "title": {"type": "string"},
            "identifier": {"type": "string"},
            "description": {"type": "string"},
            "tags": {
                "type": "any",
            },
        },
    }

    try:
        tagset = dictconfig.resolve(tagset, schema)
    except dictconfig.exceptions.ResolutionError as exc:
        raise ConfigError(None, str(exc))

    if isinstance(tagset["tags"], str):
        tags = tagset["tags"]
        if tags not in _SPECIAL_TAGSETS:
            raise ConfigError(
                None,
                f"Special tagset {tags} does not exist.",
            )
    else:
        tags_schema = {
            "type": "list",
            "element_schema": {
                "type": "string",
            },
        }

        try:
            tags = set(dictconfig.resolve(tagset["tags"], tags_schema))
        except dictconfig.exceptions.ResolutionError as exc:
            raise ConfigError(None, str(exc))

    return TagSet(
        title=tagset["title"],
        identifier=tagset["identifier"],
        description=tagset["description"],
        tags=tags,
    )


def _load_config(path: pathlib.Path) -> Config:
    """Reads a configuration file from disk.

    The configuration file is validated and defaults are applied. If the
    configuration file is invalid, a :class:`ConfigError` is raised.

    Parameters
    ----------
    path : pathlib.Path
        The path to the configuration file.

    Returns
    -------
    Config
        The configuration object.

    Raises
    ------
    ConfigError
        If the configuration file is invalid.

    """

    schema = {
        "type": "dict",
        "optional_keys": {
            "description": {"type": "string", "nullable": True, "default": None},
            "tagsets": {
                "type": "list",
                "default": {},
                "element_schema": {"type": "any"},
            },
        },
    }

    if not path.exists():
        raise ConfigError(path, f"File does not exist.")

    with path.open() as fileob:
        config = yaml.safe_load(fileob)

    try:
        config = dictconfig.resolve(config, schema)
    except dictconfig.exceptions.ResolutionError as exc:
        raise ConfigError(path, str(exc))

    try:
        tagsets = {ts["identifier"]: _make_tagset(ts) for ts in config["tagsets"]}
    except ConfigError as exc:
        raise ConfigError(path, str(exc.message))

    return Config(
        description=config["description"],
        tagsets=tagsets,
    )


# problem(s) loader ===================================================================


def _read_problem_metadata(metadata: str) -> dict:
    """Reads a YAML frontmatter string and returns a dictionary of the metadata.

    The YAML is validated and defaults are applied. If the YAML is invalid,
    a dictconfig.exceptions.ResolutionError is raised.

    Parameters
    ----------
    metadata : str
        The YAML frontmatter string.

    Returns
    -------
    dict
        The metadata dictionary.

    """
    metadata = yaml.safe_load(metadata)
    schema = {
        "type": "dict",
        "optional_keys": {
            "tags": {
                "type": "list",
                "element_schema": {
                    "type": "string",
                },
                "default": [],
            },
            "source": {
                "type": "string",
                "nullable": True,
                "default": None,
            },
        },
    }

    return dictconfig.resolve(metadata, schema)


def _load_dsctex_problem(problem_directory: pathlib.Path) -> Problem:
    """Loads a problem in DSCTeX LaTeX format from disk.

    The file may contain YAML frontmatter at the top of the file. If so,
    all lines at the top of the file that start with %% are considered
    part of the frontmatter. The rest of the file is considered the problem
    source.

    Parameters
    ----------
    problem_directory : pathlib.Path
        The path to the problem directory.

    Returns
    -------
    Problem
        The problem object.

    Raises
    ------
    ProblemError
        If there is an issue with the problem.

    """
    with (problem_directory / "problem.tex").open() as fileob:
        raw_source = fileob.read()

    # the first few lines of the file starting with %% are yaml frontmatter;
    # the rest is the problem source
    lines = raw_source.splitlines()

    frontmatter_lines = itertools.takewhile(lambda line: line.startswith("%%"), lines)
    # remove the leading %% from the frontmatter lines
    frontmatter = "\n".join(line.lstrip("% ") for line in frontmatter_lines).strip()

    if frontmatter:
        try:
            metadata = _read_problem_metadata(frontmatter)
        except dictconfig.exceptions.ResolutionError as exc:
            raise ProblemError(
                problem_directory.name,
                f"Issue with metadata. {str(exc)}",
            )
    else:
        metadata = {
            "tags": {},
            "source": None,
        }

    latex_source = "\n".join(
        itertools.dropwhile(lambda line: line.startswith("%%"), lines)
    ).strip()

    return Problem(
        identifier=problem_directory.name,
        contents=latex_source,
        path=problem_directory,
        tags=set(metadata["tags"]),
        source=metadata["source"],
        format="dsctex",
    )


def _load_gsmd_problem(problem_directory: pathlib.Path) -> Problem:
    """Load a problem in Gradescope markdown format.

    The file may contain YAML frontmatter. If so, the first line of the file must
    be three dashes (---). The text up until the next three dashes is assumed to be
    YAML frontmatter.

    Parameters
    ----------
    problem_directory : pathlib.Path
        The directory containing the problem.

    Returns
    -------
    Problem
        The problem object.

    Raises
    ------
    ProblemError
        If there is an issue with the problem.

    """

    with (problem_directory / "problem.md").open() as fileob:
        raw_source = fileob.read()

    # the first few lines of the file might be yaml frontmatter;
    # the rest is the problem source.
    # frontmatter is present if the first line is three dashes (---)
    # the text up until the next three dashes is assumed to be yaml frontmatter
    lines = raw_source.splitlines()

    if lines[0] == "---":
        frontmatter_lines = list(
            itertools.takewhile(
                lambda line: line != "---", itertools.islice(lines, 1, None)
            )
        )
        frontmatter = "\n".join(frontmatter_lines)

        try:
            metadata = _read_problem_metadata(frontmatter)
        except dictconfig.exceptions.ResolutionError as exc:
            raise ProblemError(
                problem_directory.name,
                f"File contains invalid YAML frontmatter. {exc}",
            )

        n_frontmatter_lines = len(frontmatter_lines) + 2
        markdown_source = "\n".join(lines[n_frontmatter_lines:]).strip()
    else:
        metadata = {
            "tags": {},
            "source": None,
        }
        markdown_source = raw_source

    return Problem(
        identifier=problem_directory.name,
        contents=markdown_source,
        path=problem_directory,
        tags=set(metadata["tags"]),
        source=metadata["source"],
        format="gsmd",
    )


def _load_problem(problem_directory: pathlib.Path) -> Problem:
    """Load a single problem from the problem directory.

    Parameters
    ----------
    problem_directory : pathlib.Path
        The directory containing the problem.

    Returns
    -------
    Problem
        The problem.

    Raises
    ------
    ProblemError
        If there is an issue with the problem.

    Notes
    -----
    A problem directory cannot contain both a problem.tex and a problem.md file,
    but it must contain one of them. Problems may optionally contain metadata
    at the top of the file in the form of YAML frontmatter.

    """
    if (problem_directory / "problem.tex").exists() and (
        problem_directory / "problem.md"
    ).exists():
        raise ProblemError(
            problem_directory.name,
            f"Problem directory {problem_directory} contains both problem.tex and problem.md.",
        )

    if (problem_directory / "problem.tex").exists():
        return _load_dsctex_problem(problem_directory)
    elif (problem_directory / "problem.md").exists():
        return _load_gsmd_problem(problem_directory)
    else:
        raise ProblemError(
            problem_directory.name,
            f"Problem directory {problem_directory} does not contain a problem.tex or problem.md file.",
        )


def _load_problems(
    root: pathlib.Path, raise_on_error=True
) -> typing.Generator[typing.Union[Problem, ProblemError], None, None]:
    """Loads the problems in the given root directory.

    Parameters
    ----------
    root : pathlib.Path
        The root directory of the practice bank.
    raise_on_error : bool, optional
        If True, raise an exception if there is an error loading a problem. If
        False, exceptions are yielded.

    Yields
    ------
    Problem
        The loaded problem.
    ProblemError
        If `raise_on_error` is False, exceptions are yielded instead of raised.

    """

    for path in sorted(root.iterdir()):
        if not path.is_dir():
            continue

        if path.name.startswith(".") or path.name.startswith("_"):
            continue

        # raise if the directory name is not a number
        if not path.name.isnumeric():
            raise ProblemError(
                path.name,
                f"Name of problem in directory {path} is not a number.",
            )

        try:
            yield _load_problem(path)
        except ProblemError as exc:
            if raise_on_error:
                raise
            else:
                yield exc


# load() ===============================================================================


def _check_for_duplicate_identifiers(problems: typing.List[Problem]):
    """Check for duplicate problem identifiers."""
    identifiers = set()
    for problem in problems:
        if int(problem.identifier) in identifiers:
            raise ProblemError(
                problem.identifier,
                f"Duplicate problem identifier {problem.identifier} in {problem.path}.",
            )
        else:
            identifiers.add(int(problem.identifier))


def load(root: pathlib.Path, raise_on_error=True) -> PracticeBank:
    """Loads a bank of practice problems.

    Parameters
    ----------
    root : pathlib.Path
        The root directory of the practice bank.
    raise_on_error : bool, optional
        If True, raise an exception if there is an error loading the practice
        bank. If False, exceptions are caught and returned in the
        `invalid_problems` attribute of the returned :class:`PracticeBank`
        object.

    Returns
    -------
    PracticeBank
        The loaded practice bank.

    """
    config = _load_config(root / "practicebank.yaml")

    all_problems = list(_load_problems(root, raise_on_error=raise_on_error))
    good_problems = [p for p in all_problems if isinstance(p, Problem)]
    bad_problems = [p for p in all_problems if isinstance(p, ProblemError)]

    _check_for_duplicate_identifiers(good_problems)

    return PracticeBank(
        config=config,
        problems=good_problems,
        invalid_problems=bad_problems,
        root=root,
    )
