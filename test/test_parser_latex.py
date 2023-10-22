from textwrap import dedent

from practicebank.parsers.latex import parse
from practicebank import types


def test_parses_empty_problem():
    tree = parse(r"\begin{prob}\end{prob}")

    assert tree == types.Problem()


def test_parses_problem_with_text_inside():
    tree = parse(r"\begin{prob}hello world\end{prob}")

    expected = types.Problem()
    expected.add_child(types.NormalText("hello world"))

    assert tree == expected


def test_parses_problem_with_two_paragraphs():
    tree = parse(
        dedent(
            r"""
            \begin{prob}
               hello world

               goodbye world
             \end{prob}
           """
        )
    )

    assert tree == types.Problem(
        children=[
            types.NormalText("\n   hello world\n\n   goodbye world\n "),
        ],
    )


def test_parses_problem_with_bold_text():
    tree = parse(
        dedent(
            r"""
            \begin{prob}
                hello \textbf{world}
            \end{prob}
            """
        )
    )

    assert tree == types.Problem(
        children=[
            types.NormalText("\n    hello "),
            types.BoldText("world"),
        ]
    )


def parses_problem_with_italic_text():
    tree = parse(
        dedent(
            r"""
            \begin{prob}
                hello \textit{world}
            \end{prob}
            """
        )
    )

    assert tree == types.Problem(
        children=[
            types.NormalText("\n    hello "),
            types.ItalicText("world"),
        ]
    )


def test_parses_problem_with_inline_math():
    tree = parse(
        dedent(
            r"""
            \begin{prob}
                hello $f(x) = 42$
            \end{prob}
            """
        )
    )

    assert tree == types.Problem(
        children=[
            types.NormalText("\n    hello "),
            types.InlineMath("f(x) = 42"),
        ]
    )


def test_parses_problem_with_dollar_dollar_math():
    tree = parse(
        dedent(
            r"""
            \begin{prob}
                hello $$f(x) = 42$$
            \end{prob}
            """
        )
    )

    assert tree == types.Problem(
        children=[
            types.NormalText("\n    hello "),
            types.DisplayMath("f(x) = 42"),
        ]
    )


def test_parses_problem_with_display_math():
    tree = parse(
        dedent(
            r"""
            \begin{prob}
                hello \[f(x) = 42\]
            \end{prob}
            """
        )
    )

    assert tree == types.Problem(
        children=[
            types.NormalText("\n    hello "),
            types.DisplayMath("f(x) = 42"),
        ]
    )


def test_parses_problem_with_minted_code_block():
    tree = parse(
        dedent(
            r"""
            \begin{prob}
                \begin{minted}{python}
                def f(x):
                    return x + 1
                \end{minted}
            \end{prob}
            """
        )
    )

    assert tree == types.Problem(
        children=[
            types.Code(
                "python",
                dedent(
                    r"""
                def f(x):
                    return x + 1
                """
                ),
            ),
        ]
    )


def test_parses_problem_with_mintinline_code():
    tree = parse(
        dedent(
            r"""
            \begin{prob}
                \mintinline{python}{def f(x): return x + 1}
            \end{prob}
            """
        )
    )

    assert tree == types.Problem(
        children=[
            types.InlineCode("python", "def f(x): return x + 1"),
        ]
    )


def test_problem_with_multiple_choices():
    tree = parse(
        dedent(
            r"""
            \begin{prob}
                \begin{choices}
                    \choice hello \textbf{world}
                    \choice goodbye world
                    \correctchoice goodbye world
                \end{choices}
            \end{prob}
            """
        )
    )

    assert tree == types.Problem(
        children=[
            types.MultipleChoices(
                children=[
                    types.Choice(
                        children=[
                            types.NormalText(" hello "),
                            types.BoldText("world"),
                        ]
                    ),
                    types.Choice(
                        children=[
                            types.NormalText(" goodbye world\n        "),
                        ]
                    ),
                    types.Choice(
                        children=[
                            types.NormalText(" goodbye world\n    "),
                        ],
                        correct=True,
                    ),
                ]
            )
        ]
    )


def test_problem_with_multiple_select():
    tree = parse(
        dedent(
            r"""
            \begin{prob}
                \begin{choices}[rectangle]
                    \choice hello \textbf{world}
                    \choice goodbye world
                    \correctchoice goodbye world
                \end{choices}
            \end{prob}
            """
        )
    )

    assert tree == types.Problem(
        children=[
            types.MultipleSelect(
                children=[
                    types.Choice(
                        children=[
                            types.NormalText(" hello "),
                            types.BoldText("world"),
                        ]
                    ),
                    types.Choice(
                        children=[
                            types.NormalText(" goodbye world\n        "),
                        ]
                    ),
                    types.Choice(
                        children=[
                            types.NormalText(" goodbye world\n    "),
                        ],
                        correct=True,
                    ),
                ]
            )
        ]
    )


def test_problem_with_code_in_multiple_choice():
    tree = parse(
        dedent(
            r"""
            \begin{prob}
                \begin{choices}
                    \choice hello \textbf{world}
                    \choice \begin{minted}{python}
                    def f(x):
                        return x + 1
                    \end{minted}
                \end{choices}
            \end{prob}
            """
        )
    )

    assert tree == types.Problem(
        children=[
            types.MultipleChoices(
                children=[
                    types.Choice(
                        children=[
                            types.NormalText(" hello "),
                            types.BoldText("world"),
                        ]
                    ),
                    types.Choice(
                        children=[
                            types.Code(
                                "python",
                                dedent(
                                    r"""
                                def f(x):
                                    return x + 1
                                """
                                ),
                            ),
                        ],
                    ),
                ]
            )
        ]
    )


def test_problem_with_solution():
    tree = parse(
        dedent(
            r"""
            \begin{prob}
                hello world
                \begin{soln}
                    goodbye world
                \end{soln}
            \end{prob}
            """
        )
    )

    assert tree == types.Problem(
        children=[
            types.NormalText("\n    hello world\n    "),
            types.Solution(
                children=[
                    types.NormalText("\n        goodbye world\n    "),
                ]
            ),
        ]
    )


def test_problem_with_Tf():
    tree = parse(
        dedent(
            r"""
            \begin{prob}
                hello world
                \Tf{}
            \end{prob}
            """
        )
    )

    assert tree == types.Problem(
        children=[
            types.NormalText("\n    hello world\n    "),
            types.TrueFalse(solution=True),
        ]
    )


def test_problem_with_tF():
    tree = parse(
        dedent(
            r"""
            \begin{prob}
                hello world
                \tF{}
            \end{prob}
            """
        )
    )

    assert tree == types.Problem(
        children=[
            types.NormalText("\n    hello world\n    "),
            types.TrueFalse(solution=False),
        ]
    )


def test_problem_with_inline_response_box():
    tree = parse(
        dedent(
            r"""
            \begin{prob}
                What is the \textbf{worst case} time complexity of the function in the last problem?
                State your answer using asymptotic notation.

                \inlineresponsebox{$\Theta(n^2)$}

            \end{prob}
               """
        )
    )

    assert tree == types.Problem(
        children=[
            types.NormalText(
                "\n    What is the ",
            ),
            types.BoldText("worst case"),
            types.NormalText(
                " time complexity of the function in the last problem?\n    State your answer using asymptotic notation.\n\n    ",
            ),
            types.FillInTheBlank(
                children=[
                    types.InlineMath("\\Theta(n^2)"),
                ]
            ),
        ]
    )


def test_includegraphics(tmp_path):
    image_path = tmp_path / "image.png"
    image_path.write_text("hello world")

    tree = parse(
        dedent(
            r"""
            \begin{prob}
                \includegraphics{image.png}
            \end{prob}
            """
        ),
        path=tmp_path,
    )

    assert tree == types.Problem(
        children=[
            types.Image(
                data=b"hello world",
                relative_path="image.png",
            )
        ]
    )


def test_inputminted(tmp_path):
    code_path = tmp_path / "code.py"
    code_path.write_text("hello world")

    tree = parse(
        dedent(
            r"""
            \begin{prob}
                \inputminted{python}{code.py}
            \end{prob}
            """
        ),
        path=tmp_path,
    )

    assert tree == types.Problem(
        children=[
            types.Code(
                "python",
                "hello world",
            )
        ]
    )


def test_subproblems():
    tree = parse(
        dedent(
            r"""
            \begin{prob}
                This is the problem.

                \begin{subprobset}
                    \begin{subprob}
                        hello world
                    \end{subprob}

                    \begin{subprob}
                        goodbye world
                    \end{subprob}
                \end{subprobset}
            \end{prob}
            """
        )
    )

    assert tree == types.Problem(
        children=[
            types.NormalText("\n    This is the problem.\n\n    "),
            types.Subproblem(
                children=[
                    types.NormalText("\n        hello world\n    "),
                ]
            ),
            types.Subproblem(
                children=[
                    types.NormalText("\n        goodbye world\n    "),
                ]
            ),
        ]
    )
