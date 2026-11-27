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


def test_choice_inputs_align_with_first_line_of_text(example_1, tmpdir):
    """A wrapped choice's radio button or checkbox sits level with its first line."""
    out = pathlib.Path(tmpdir / "out")
    build(example_1, out)

    html = (out / "all.html").read_text()
    style = html[html.index("<style>") : html.index("</style>")]
    assert "align-items: baseline" in style
    assert "align-items: center" not in style


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


def test_minted_language_is_read_when_options_are_given(tmpdir):
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
                \begin{minted}[autogobble]{python}
                    print(1)
                \end{minted}
            \end{prob}
            """
        ).strip(),
    )

    out = pathlib.Path(tmpdir / "out")
    build(root, out, fragment=True)

    html = (out / "tags" / "code.html").read_text()
    assert '<code class="language-python">print(1)</code>' in html


# badges -------------------------------------------------------------------------------


@fixture()
def badged(tmpdir):
    """A practicebank where "hard" is a badge."""
    root = pathlib.Path(tmpdir) / "badged"
    example = Example(root)

    example.write_config(
        {
            "tagsets": [
                {
                    "identifier": "quiz-01",
                    "title": "Quiz 01",
                    "description": "Quiz 01.",
                    "tags": ["recursion", "hard"],
                },
                {
                    "identifier": "all",
                    "title": "All",
                    "description": "All.",
                    "tags": "__ALL__",
                },
            ],
            "badges": [
                {"tag": "hard", "symbol": "🌶️", "title": "One of the hardest problems"}
            ],
        }
    )

    # hard, with another tag
    example.write_problem("01", "gsmd", "---\ntags: [recursion, hard]\n---\nOne.")
    # not hard
    example.write_problem("02", "gsmd", "---\ntags: [recursion]\n---\nTwo.")
    # hard, and no other tags
    example.write_problem("03", "gsmd", "---\ntags: [hard]\n---\nThree.")
    # not hard, in another topic
    example.write_problem("04", "gsmd", "---\ntags: [graphs]\n---\nFour.")

    return root


def _problem_html(page: str, identifier: str) -> str:
    """The HTML of one problem on a page, from its opening div to the next one."""
    start = page.index(f"Problem #{identifier}")
    start = page.rindex('<div class="problem-outer"', 0, start)
    end = page.find('<div class="problem-outer"', start + 1)
    return page[start:] if end == -1 else page[start:end]


def test_badge_tag_has_no_tag_page(badged, tmpdir):
    out = pathlib.Path(tmpdir / "out")
    build(badged, out)

    assert not (out / "tags" / "hard.html").exists()
    assert (out / "tags" / "recursion.html").exists()


def test_badge_tag_is_not_listed_on_index_or_tagset_pages(badged, tmpdir):
    out = pathlib.Path(tmpdir / "out")
    build(badged, out)

    for page in ["index.html", "quiz-01.html", "all.html"]:
        assert "tags/hard.html" not in (out / page).read_text()


def test_badge_tag_is_not_in_problem_tags_line(badged, tmpdir):
    out = pathlib.Path(tmpdir / "out")
    build(badged, out)

    page = (out / "all.html").read_text()
    one = _problem_html(page, "01")
    assert "Tags: <a href='./tags/recursion.html'>recursion</a></p>" in one
    assert ">hard<" not in one

    # a problem whose only tag is a badge has no "Tags:" line at all
    assert "Tags:" not in _problem_html(page, "03")


def test_badge_symbol_follows_problem_number(badged, tmpdir):
    out = pathlib.Path(tmpdir / "out")
    build(badged, out)

    page = (out / "all.html").read_text()
    one = _problem_html(page, "01")
    assert '<div class="problem-outer" data-badges="hard">' in one
    assert "<h2>Problem #01 <span" in one
    assert 'title="One of the hardest problems"' in one
    assert 'aria-label="One of the hardest problems"' in one
    assert "🌶️</span></h2>" in one

    two = _problem_html(page, "02")
    assert "data-badges" not in two
    assert "🌶️" not in two
    assert "<h2>Problem #02</h2>" in two


def test_badged_problems_appear_where_their_other_tags_put_them(badged, tmpdir):
    out = pathlib.Path(tmpdir / "out")
    build(badged, out)

    recursion = (out / "tags" / "recursion.html").read_text()
    assert "Problem #01" in recursion
    assert "Problem #03" not in recursion

    # quiz-01 lists "hard" as a tag, but a badge doesn't select problems
    quiz = (out / "quiz-01.html").read_text()
    assert "Problem #01" in quiz and "Problem #02" in quiz
    assert "Problem #03" not in quiz

    assert "Problem #03" in (out / "all.html").read_text()


def test_filter_is_on_problem_pages_when_badges_are_configured(badged, tmpdir):
    for fragment in [False, True]:
        out = pathlib.Path(tmpdir / f"out-{fragment}")
        build(badged, out, fragment=fragment)

        for page in [out / "quiz-01.html", out / "all.html", out / "tags" / "graphs.html"]:
            html = page.read_text()
            assert '<div class="practicebank-filter"' in html
            assert 'data-only="hard"' in html
            assert 'role="switch" aria-checked="false" data-only="hard"' in html
            assert '<span class="practicebank-switch" aria-hidden="true"></span>' in html
            assert "🌶️ only</span></button>" in html
            # one switch per badge, and no separate "All" button
            assert html.count("<button") == 1
            assert "practicebank-only" in html  # the script's localStorage key
            # a toggle moves the switch first and filters after its slide
            assert "SLIDE_MS" in html and "requestAnimationFrame" in html
            assert '<p class="practicebank-empty" data-only="hard" hidden>' in html

        # the index lists no problems, so it has no filter
        assert "practicebank-filter" not in (out / "index.html").read_text()


def test_filter_is_absent_without_badges(example_1, tmpdir):
    for fragment in [False, True]:
        out = pathlib.Path(tmpdir / f"out-{fragment}")
        build(example_1, out, fragment=fragment)

        for page in [out / "all.html", out / "tags" / "recursion.html"]:
            html = page.read_text()
            assert "practicebank-filter" not in html
            assert "practicebank-only" not in html
            assert "data-badges" not in html


def _build_unlabelled_code_block(tmpdir, config):
    root = pathlib.Path(tmpdir) / "example"
    example = Example(root)
    example.write_config(config)
    example.write_problem(
        "01",
        "gsmd",
        dedent(
            """
            ---
            tags: [code]
            ---
            ```
            print(1)
            ```
            """
        ).strip(),
    )

    out = pathlib.Path(tmpdir / "out")
    build(root, out, fragment=True)
    return (out / "tags" / "code.html").read_text()


def test_code_blocks_without_a_language_have_no_language_by_default(tmpdir):
    html = _build_unlabelled_code_block(tmpdir, {"tagsets": []})
    assert "<code>print(1)</code>" in html
    assert "language-" not in html


def test_code_blocks_without_a_language_use_the_default_code_language(tmpdir):
    html = _build_unlabelled_code_block(
        tmpdir, {"tagsets": [], "default_code_language": "python"}
    )
    assert '<code class="language-python">print(1)</code>' in html


def test_filter_label_can_be_configured(tmpdir):
    root = pathlib.Path(tmpdir) / "labelled"
    example = Example(root)
    example.write_config(
        {
            "tagsets": [],
            "badges": [
                {
                    "tag": "hard",
                    "symbol": "🌶️",
                    "filter_label": "Show only the <hardest> problems 🌶️",
                }
            ],
        }
    )
    example.write_problem("01", "gsmd", "---\ntags: [recursion, hard]\n---\nOne.")

    out = pathlib.Path(tmpdir / "out")
    build(root, out, fragment=True)

    html = (out / "tags" / "recursion.html").read_text()
    assert (
        '<span class="practicebank-switch-label">'
        "Show only the &lt;hardest&gt; problems 🌶️</span>"
    ) in html
    assert "🌶️ only" not in html
