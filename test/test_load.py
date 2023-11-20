import pathlib
from textwrap import dedent

import yaml

from pytest import fixture, raises

import practicebank
from practicebank import exceptions

from util import Example

# examples =============================================================================


@fixture()
def example_1(tmpdir):
    """A totally-fine practicebank."""
    root = pathlib.Path(tmpdir) / "example_1"

    example = Example(root)

    example.write_config(
        {
            "description": "A totally-fine practicebank.",
            "tagsets": [
                {
                    "identifier": "midterm01",
                    "title": "Midterm 01",
                    "description": "Practice for Midterm 01.",
                    "tags": ["time complexity", "asymptotic notation", "recursion"],
                },
                {
                    "identifier": "midterm02",
                    "title": "Midterm 02",
                    "description": "Practice for Midterm 02.",
                    "tags": ["graph search", "graph theory"],
                },
                {
                    "identifier": "all",
                    "title": "All Tags",
                    "description": "All tags.",
                    "tags": "__ALL__",
                },
            ],
        },
    )

    example.write_problem(
        "01",
        "dsctex",
        dedent(
            r"""
            %% tags: [graph theory]
            %% source: 2023-wi-midterm_01

            \begin{prob}
                This is the first problem.
            \end{prob}
        """
        ).strip(),
    )

    example.write_problem(
        "02",
        "gsmd",
        dedent(
            r"""
            ---
            tags: [time complexity, asymptotic notation, recursion]
            source: 2023-wi-midterm_01
            ---
            This is the second problem.
        """
        ).strip(),
    )

    example.write_problem(
        "03",
        "dsctex",
        dedent(
            r"""
                \begin{prob}
                    This is the third problem. There is no yaml frontmatter.
                \end{prob}
            """
        ).strip(),
    )

    example.write_problem(
        "04",
        "gsmd",
        dedent(
            r"""
                This is the fourth problem. There is no yaml frontmatter.
            """
        ).strip(),
    )

    return root


# tests ================================================================================

# problems -----------------------------------------------------------------------------


def test_tagsets_are_in_order_they_appear_in_config(example_1):
    pb = practicebank.io.load(example_1)
    assert list(pb.config.tagsets) == ["midterm01", "midterm02", "all"]


def test_ignores_directories_starting_with_underscore(example_1):
    (example_1 / "_ignore_me").mkdir()
    pb = practicebank.io.load(example_1)
    assert len(pb.problems) == 4


def test_ignores_directories_starting_with_dot(example_1):
    (example_1 / ".ignore_me").mkdir()
    pb = practicebank.io.load(example_1)
    assert len(pb.problems) == 4


def test_problems_are_sorted_by_identifier(example_1):
    pb = practicebank.io.load(example_1)
    assert [p.identifier for p in pb.problems] == ["01", "02", "03", "04"]


def test_loads_dsctex_problem_with_metadata(example_1):
    pb = practicebank.io.load(example_1)

    assert len(pb.problems) == 4

    assert pb.problems[0].identifier == "01"
    assert pb.problems[0].format == "dsctex"
    assert pb.problems[0].tags == {"graph theory"}
    assert pb.problems[0].source == "2023-wi-midterm_01"
    assert (
        pb.problems[0].contents
        == dedent(
            r"""
            \begin{prob}
                This is the first problem.
            \end{prob}
        """
        ).strip()
    )


def test_loads_gsmd_problem_with_metadata(example_1):
    pb = practicebank.io.load(example_1)

    assert len(pb.problems) == 4

    assert pb.problems[1].identifier == "02"
    assert pb.problems[1].format == "gsmd"
    assert pb.problems[1].tags == {
        "time complexity",
        "asymptotic notation",
        "recursion",
    }
    assert pb.problems[1].source == "2023-wi-midterm_01"
    assert (
        pb.problems[1].contents
        == dedent(
            r"""
            This is the second problem.
        """
        ).strip()
    )


def test_loads_dsctex_problem_without_metadata(example_1):
    pb = practicebank.io.load(example_1)

    assert len(pb.problems) == 4

    assert pb.problems[2].identifier == "03"
    assert pb.problems[2].format == "dsctex"
    assert pb.problems[2].tags == set()
    assert pb.problems[2].source == None
    assert (
        pb.problems[2].contents
        == dedent(
            r"""
                \begin{prob}
                    This is the third problem. There is no yaml frontmatter.
                \end{prob}
            """
        ).strip()
    )


def test_loads_gsmd_problem_without_metadata(example_1):
    pb = practicebank.io.load(example_1)

    assert len(pb.problems) == 4

    assert pb.problems[3].identifier == "04"
    assert pb.problems[3].format == "gsmd"
    assert pb.problems[3].tags == set()
    assert pb.problems[3].source == None
    assert (
        pb.problems[3].contents
        == dedent(
            r"""
                This is the fourth problem. There is no yaml frontmatter.
            """
        ).strip()
    )


# configuration ------------------------------------------------------------------------


def test_reads_configuration(example_1):
    pb = practicebank.io.load(example_1)

    assert pb.config.description == "A totally-fine practicebank."
    assert pb.config.tagsets["midterm01"].title == "Midterm 01"
    assert pb.config.tagsets["midterm01"].description == "Practice for Midterm 01."
    assert pb.config.tagsets["midterm01"].tags == {
        "time complexity",
        "asymptotic notation",
        "recursion",
    }

    assert pb.config.tagsets["all"].tags == "__ALL__"


def test_configuration_without_description(tmpdir):
    root = pathlib.Path(tmpdir / "example")
    example = Example(root)

    example.write_config({"tagsets": []})

    pb = practicebank.io.load(root)
    pb.config.description is None


def test_configuration_without_tagsets(tmpdir):
    root = pathlib.Path(tmpdir / "example")
    example = Example(root)

    example.write_config({"description": "A fine config."})

    pb = practicebank.io.load(root)
    assert pb.config.tagsets == {}


# error handling -----------------------------------------------------------------------


def test_raises_if_configuration_does_not_exist(tmpdir):
    root = pathlib.Path(tmpdir / "example")
    example = Example(root)

    with raises(exceptions.ConfigError):
        practicebank.io.load(root)


def test_raises_if_configuration_has_extra_keys(tmpdir):
    root = pathlib.Path(tmpdir / "example")
    example = Example(root)

    example.write_config(
        {"foo": "unknown", "description": "A bad config.", "tagsets": ["one", "two"]}
    )

    with raises(exceptions.ConfigError):
        practicebank.io.load(root)


def test_raises_if_configuration_contains_an_unknown_special_tagset(tmpdir):
    root = pathlib.Path(tmpdir / "example")
    example = Example(root)

    example.write_config(
        {
            "description": "A fine config.",
            "tagsets": [
                {
                    "identifier": "unknown",
                    "title": "Unknown Tags",
                    "description": "Unknown tags.",
                    "tags": "__UNKNOWN__",
                },
            ],
        }
    )

    with raises(exceptions.ConfigError):
        practicebank.io.load(root)


def test_raises_if_there_are_multiple_problem_formats_in_the_same_problem_directory(
    tmpdir,
):
    root = pathlib.Path(tmpdir / "example")
    example = Example(root)

    example.write_problem(
        "01",
        "gsmd",
        dedent(
            r"""
                This is the first problem.
            """
        ).strip(),
    )

    example.write_problem(
        "01",
        "dsctex",
        dedent(
            r"""
                \begin{prob}
                    This is also the first problem.
                \end{prob}
            """
        ).strip(),
        exist_ok=True,
    )

    example.write_config({"description": "A fine config.", "tagsets": []})

    with raises(exceptions.ProblemError):
        practicebank.io.load(root)


def test_raises_if_problem_directory_is_missing_a_problem(tmpdir):
    root = pathlib.Path(tmpdir / "example")
    example = Example(root)

    example.write_config({"description": "A fine config.", "tagsets": []})

    (root / "01").mkdir()

    with raises(exceptions.ProblemError):
        practicebank.io.load(root)


def test_raises_if_gsmd_problem_metadata_contains_extra_keys(tmpdir):
    root = pathlib.Path(tmpdir / "example")
    example = Example(root)

    example.write_problem(
        "01",
        "gsmd",
        dedent(
            r"""
                ---
                tags: [graph theory]
                foo: bar
                ---
                This is the first problem.
            """
        ).strip(),
    )

    example.write_config({"description": "A fine config.", "tagsets": []})

    with raises(exceptions.ProblemError):
        practicebank.io.load(root)


def test_raises_if_dsctex_problem_metadata_contains_extra_keys(tmpdir):
    root = pathlib.Path(tmpdir / "example")
    example = Example(root)

    example.write_problem(
        "01",
        "dsctex",
        dedent(
            r"""
                %% tags: [graph theory]
                %% foo: bar
                \begin{prob}
                    This is the first problem.
                \end{prob}
            """
        ).strip(),
    )

    example.write_config({"description": "A fine config.", "tagsets": []})

    with raises(exceptions.ProblemError):
        practicebank.io.load(root)
