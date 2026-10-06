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


def test_build_standalone_writes_full_documents(example_1, tmpdir):
    out = pathlib.Path(tmpdir / "out")
    build(example_1, out)

    html = (out / "all.html").read_text()
    assert html.startswith("<!DOCTYPE html>")
    assert "MathJax" in html


def test_build_fragment_omits_document_wrapper_and_scripts(example_1, tmpdir):
    out = pathlib.Path(tmpdir / "out")
    build(example_1, out, fragment=True)

    for path in [out / "index.html", out / "all.html", out / "tags" / "recursion.html"]:
        html = path.read_text()
        for forbidden in ["<!DOCTYPE", "<html", "<head", "<body", "MathJax", "highlight"]:
            assert forbidden not in html


def test_build_fragment_includes_choice_styles(example_1, tmpdir):
    out = pathlib.Path(tmpdir / "out")
    build(example_1, out, fragment=True)

    html = (out / "all.html").read_text()
    assert "<style>" in html
    assert ".multiple-choices .choice label" in html


def test_build_fragment_with_template_raises(example_1, tmpdir):
    out = pathlib.Path(tmpdir / "out")
    with raises(ValueError):
        build(example_1, out, template="{body}", fragment=True)


def test_code_blocks_have_language_class_and_no_surrounding_blank_lines(tmpdir):
    root = pathlib.Path(tmpdir) / "example"
    example = Example(root)
    example.write_config({"tagsets": []})
    example.write_problem(
        "01",
        "dsctex",
        dedent(
            r"""
            %% tags: [code]

            \begin{prob}
                \begin{minted}{python}

                    if x < 1:
                        print(x)

                \end{minted}
            \end{prob}
            """
        ).strip(),
    )

    out = pathlib.Path(tmpdir / "out")
    build(root, out, fragment=True)

    html = (out / "tags" / "code.html").read_text()
    assert (
        '<pre class="code"><code class="language-python">'
        "if x &lt; 1:\n    print(x)</code></pre>"
    ) in html


def test_math_uses_default_mathjax_delimiters(tmpdir):
    root = pathlib.Path(tmpdir) / "example"
    example = Example(root)
    example.write_config({"tagsets": []})
    example.write_problem(
        "01",
        "dsctex",
        dedent(
            r"""
            %% tags: [math]

            \begin{prob}
                Inline $x^2$ and display \[ y^2 \] and aligned:
                \begin{align*}
                    a &= b
                \end{align*}
            \end{prob}
            """
        ).strip(),
    )

    out = pathlib.Path(tmpdir / "out")
    build(root, out, fragment=True)

    html = (out / "tags" / "math.html").read_text()
    assert r"\(x^2\)" in html
    assert r"\[ y^2 \]" in html or r"\[y^2\]" in html
    assert r"\[\begin{align*}" in html
    assert "$" not in html
