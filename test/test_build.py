import pathlib
from textwrap import dedent

from pytest import fixture, raises

from util import Example

from practicebank import build

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


def test_build(example_1, tmpdir):
    out = pathlib.Path(tmpdir / "out")
    build(example_1, out)
