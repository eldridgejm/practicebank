"""Parses problems written in LaTeX."""

import textwrap
import pathlib
import typing

from .. import types

import TexSoup
import TexSoup.data

ENV_PARSERS = {}
CMD_PARSERS = {}


class _Context(typing.NamedTuple):
    # path to the directory containing the problem being parsed
    path: typing.Optional[pathlib.Path]


def _env_parser(name: str):
    def decorator(fn):
        ENV_PARSERS[name] = fn
        return fn

    return decorator


def _cmd_parser(name: str):
    def decorator(fn):
        CMD_PARSERS[name] = fn
        return fn

    return decorator


@_env_parser("[tex]")
def _(node: TexSoup.data.TexNode, context: _Context):
    [child] = node.contents
    return _convert_soup_node(child, context)


@_env_parser("prob")
def _(tex_node: TexSoup.data.TexNode, context: _Context):
    problem = types.Problem()
    for tex_child in tex_node:
        if hasattr(tex_child, "name") and tex_child.name == "subprobset":
            for tex_grandchild in tex_child.contents:
                problem.add_child(_convert_soup_node(tex_grandchild, context=context))
        else:
            problem.add_child(_convert_soup_node(tex_child, context=context))
    return problem

@_env_parser("subprob")
def _(tex_node: TexSoup.data.TexNode, context: _Context):
    return types.Subproblem(children=[_convert_soup_node(child, context=context) for child in tex_node.contents])

@_cmd_parser("textbf")
def _(node: TexSoup.data.TexCmd, _):
    return types.BoldText(node.string)


@_env_parser("$")
def _(node: TexSoup.data.TexNode, _):
    return types.InlineMath(node.expr.string)


@_env_parser("$$")
def _(node: TexSoup.data.TexNode, _):
    return types.DisplayMath(node.expr.string)


@_env_parser("displaymath")
def _(node: TexSoup.data.TexNode, _):
    return types.DisplayMath(node.expr.string)

@_env_parser("align")
def _(node: TexSoup.data.TexNode, _):
    return types.DisplayMath(node.expr.string)


@_env_parser("minted")
def _(node: TexSoup.data.TexNode, _):
    return types.Code(node.args[0].string, textwrap.dedent(node.expr.string))


@_cmd_parser("mintinline")
def _(node: TexSoup.data.TexCmd, _):
    return types.InlineCode(node.args[0].string, node.args[1].string)


@_env_parser("soln")
def _(node: TexSoup.data.TexNode, context: _Context):
    return types.Solution(
        children=[_convert_soup_node(child, context=context) for child in node.contents]
    )


@_cmd_parser("Tf")
def _(node: TexSoup.data.TexCmd, _):
    return types.TrueFalse(True)


@_cmd_parser("tF")
def _(node: TexSoup.data.TexCmd, _):
    return types.TrueFalse(False)


@_cmd_parser("inlineresponsebox")
def _(node: TexSoup.data.TexCmd, context: _Context):
    return types.FillInTheBlank(
        children=[_convert_soup_node(child, context=context) for child in node.contents]
    )


@_cmd_parser("includegraphics")
def _(node: TexSoup.data.TexCmd, context: _Context):
    relpath = node.args[0].string.replace(r"\thisdir/", "")

    with (context.path / relpath).open("rb") as f:
        data = f.read()

    return types.Image(relative_path=relpath, data=data)


@_cmd_parser("inputminted")
def _(node: TexSoup.data.TexCmd, context: _Context):
    relpath = node.args[1].string.replace(r"\thisdir/", "")

    with (context.path / relpath).open("r") as f:
        code = f.read()

    return types.Code(language=node.args[0].string, code=code)


def _segment(iterable, predicate):
    """Segments an iterable into sublists based on a predicate.

    Example:

        >>> lst = [5, "x", "y", "z", 2, "a", "b"]
        >>> _segment(lst, lambda x: isinstance(x, int))
        [(5, ["x", "y", "z"], 2), ["a", "b"]]

    """
    segments = []
    current_segment = []
    for item in iterable:
        if predicate(item):
            if current_segment:
                segments.append(current_segment)
                current_segment = []
        current_segment.append(item)
    if current_segment:
        segments.append(current_segment)
    return segments


@_env_parser("choices")
def _(node: TexSoup.data.TexNode, context: _Context):
    # node.contents will be a list of TexNodes. the first will be a \choice or
    # \correctchoice, followed by one or more nodes containing the contents of that
    # choice, until eventually there is another \choice or \correctchoice node. Note
    # that the \choice / \correctchoice nodes can be followed by more than one node,
    # as is the case with "\choice this is \textbf{bold}", where there are two nodes. to handle this, we'll group the nodes into lists of nodes, where each list corresponds to a single choice. We'll then convert each list of nodes into a single Choice object.

    class_ = types.MultipleChoices
    contents = node.contents

    if node.args:
        if node.args[0].string == "rectangle":
            class_ = types.MultipleSelect
            contents = node.contents[1:]

    def _is_choice(node):
        return hasattr(node, "name") and node.name in ("choice", "correctchoice")

    segments = _segment(contents, _is_choice)

    def _make_choice_from_segment(segment):
        correct = segment[0].name == "correctchoice"
        return types.Choice(
            correct=correct,
            children=[_convert_soup_node(n, context=context) for n in segment[1:]],
        )

    return class_(children=[_make_choice_from_segment(segment) for segment in segments])


def _convert_soup_node(node: TexSoup.data.TexNode, context: _Context):
    if isinstance(node, str):
        return types.NormalText(node)
    elif isinstance(node.expr, (TexSoup.data.TexNamedEnv, TexSoup.data.TexEnv)):
        parsers = ENV_PARSERS
    elif isinstance(node.expr, TexSoup.data.TexCmd):
        parsers = CMD_PARSERS
    else:
        raise ValueError(f"Unknown node type: {node.name}")

    if node.name not in parsers:
        raise ValueError(f"Unknown node type: {node.name}")

    return parsers[node.name](node, context)


def parse(latex: str, path: typing.Optional[typing.Union[str, pathlib.Path]] = None):
    """Parses a LaTeX string into a problem tree."""
    soup = TexSoup.TexSoup(latex)

    if path is not None:
        path = pathlib.Path(path)

    context = _Context(path)

    res = _convert_soup_node(soup, context)
    return res
