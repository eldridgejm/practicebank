"""Parses problems written in LaTeX."""

import textwrap
import pathlib
import typing
import itertools

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
    return types.Subproblem(
        children=[
            _convert_soup_node(child, context=context) for child in tex_node.contents
        ]
    )


@_cmd_parser("textbf")
def _(node: TexSoup.data.TexCmd, _):
    return types.BoldText(node.string)


@_cmd_parser("textit")
def _(node: TexSoup.data.TexCmd, _):
    return types.ItalicText(node.string)


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
    return types.DisplayMath("\\begin{aligned}" + node.expr.string + "\\end{aligned}")


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


def _split_text_node_by_paragraphs(node: types.NormalText):
    """Splits a text node into multiple text nodes, each containing a single paragraph."""
    paragraphs = node.text.split("\n\n")
    return [types.NormalText(paragraph) for paragraph in paragraphs]


def _paragraphize_old(node: types.InternalNode):
    def _copy(n: types.InternalNode):
        """Create a copy of a node, copying attributes but not the children."""
        copy = type(n)(**{k: getattr(n, k) for k in n.attrs})
        return copy

    node_with_paragraphs = _copy(node)

    current_paragraph = types.Paragraph()
    for child in node.children():
        if isinstance(child, types.Paragraph.allowed_child_types):
            if isinstance(child, types.NormalText):
                splits = _split_text_node_by_paragraphs(child)
                current_paragraph.add_child(splits[0])
                for split in splits[1:]:
                    node_with_paragraphs.add_child(current_paragraph)
                    current_paragraph = types.Paragraph()
                    current_paragraph.add_child(split)
            else:
                current_paragraph.add_child(child)

        else:
            if node.number_of_children() > 0:
                # add existing paragraph to node
                node_with_paragraphs.add_child(current_paragraph)
                current_paragraph = types.Paragraph()
            node_with_paragraphs.add_child(child)

            _paragraphize(child)

    if node.number_of_children() > 0:
        # add existing paragraph to node
        node_with_paragraphs.add_child(current_paragraph)

    return node_with_paragraphs


_TextLikeNode = typing.Union[
    types.TextNode,
    types.InlineMath,
    types.InlineCode,
]


def _paragraphize_textlike_nodes(
    nodes: typing.Sequence[_TextLikeNode],
) -> typing.List[types.Paragraph]:
    """Creates paragraphs out of a sequence of nodes that can be in paragraphs.

    Given a sequence of "text-like" nodes that can be in paragraphs, we need to merge
    some of them into the same paragraph, while splitting others into multiple
    paragraphs.

    For example, if we have a sequence of nodes like:

        - NormalText("This is a ")
        - BoldText("bold")
        - NormalText(" paragraph with math: ")
        - InlineMath("x^2 + y^2 = z^2")

    We need to combine these four nodes under one paragraph. But in the following sequence
    we must split the text node into two paragraphs:

        - NormalText("This is a paragraph.\n\nAnd this is another.")

    This is necessary because TexSoup does not split different paragraphs into
    different nodes. Instead, it puts them all into one node, separated by two
    newlines. We need to split this node into two separate nodes.

    Returns
    -------
    List[types.Paragraph]
        A list of paragraph objects.

    """
    # our first step is to "split" text nodes containing multiple paragraphs into multiple
    # nodes. We'll keep track of where the split was made by using a sentinel object,
    # `parbreak`:
    parbreak = object()

    # first, we create a helper function to split a single node into a list of nodes
    # and parbreaks:
    def _split_text_node_into_paragraphs(node: types.TextNode):
        """Takes a text node and looks for paragraph breaks.

        Returns a list of text nodes. The list will contain `parbreak` objects to
        represent paragraph breaks. If there are no paragraph breaks, the list
        will contain a single text node.

        """
        paragraphs = node.text.split("\n\n")
        if len(paragraphs) == 1:
            return [node]

        nodes = []
        for paragraph in paragraphs:
            nodes.append(type(node)(paragraph))
            nodes.append(parbreak)
        nodes.pop()  # remove the last break

        return nodes

    # now we do the splitting. the result of this will be an expanded list of
    # nodes with `parbreak` objects interspersed.
    nodes_after_splitting = []
    for node in nodes:
        # only text nodes can be split (inline math and code nodes can't)
        if isinstance(node, types.TextNode):
            for split_node in _split_text_node_into_paragraphs(node):
                nodes_after_splitting.append(split_node)
        else:
            nodes_after_splitting.append(node)

    # now we have a list of the form [NormalText, BoldText, parbreak, NormalText, ...]
    # we group this by splitting on the parbreaks:
    groups = itertools.groupby(nodes_after_splitting, lambda n: n is parbreak)

    # each group where the key is False is a group of nodes that should be merged
    # into a single paragraph.
    paragraphs = []
    for is_break, nodes in groups:
        if not is_break:
            paragraphs.append(types.Paragraph(children=list(nodes)))
    return paragraphs


def _paragraphize(node: types.InternalNode):
    """Creates paragraph nodes, where appropriate.

    TexSoup does not have the concept of paragraphs. Therefore, after constructing
    the tree, we need to do some post-processing to create paragraph nodes out of
    text nodes that should be split or merged.

    For example, a Prob node could have children:

        - NormalText("This is the first ")
        - BoldText("problem")
        - NormalText(" in the assignment.\n\n")
        - NormalText("It is worth 10 points.")
        - Solution(...)

    We want to merge the first three nodes into a single paragraph node. The last
    NormalText node is in a separate paragraph (due to the "\n\n"), so we'll create
    a second paragraph node for that. So the result will be

        - Paragraph(
                children=[
                    NormalText("This is the first "),
                    BoldText("problem"),
                    NormalText(" in the assignment."),
                    ]
                )
        - Paragraph(
                children=[
                    NormalText("It is worth 10 points."),
                    ]
                )
        - Solution(...)

    This function performs the fix recursively on the tree, producing a new
    tree with the same general structure but with paragraph nodes added.

    """

    # we begin by copying the current node into a new node, but without the children;
    # that is, we only copy attributes
    def _copy(n: types.InternalNode):
        """Create a copy of a node, copying attributes but not the children."""
        copy = type(n)(**{k: getattr(n, k) for k in n.attrs})
        return copy

    node_with_paragraphs = _copy(node)

    # some of the children will be text-like (NormalText, InlineMath, etc.), and need
    # to be grouped into paragraphs. Others, like Solution, should not be grouped.
    groups = itertools.groupby(
        node.children(), lambda n: isinstance(n, types.Paragraph.allowed_child_types)
    )

    # each group where the key is True is a group of nodes that could be merged
    # into a single paragraph; we do this with _paragraphize_textlike_nodes
    # each group where the key is False is a group of nodes that should not be
    # merged into a paragraph and can simply be inserted into the tree as-is. These
    # are the nodes that can be recursively processed with _paragraphize.
    for is_allowed_in_paragraph, nodes in groups:
        if is_allowed_in_paragraph:
            for paragraph in _paragraphize_textlike_nodes(nodes):
                node_with_paragraphs.add_child(paragraph)
        else:
            for node in nodes:
                # `node` could still be a leaf node at this point; if so, we don't need
                # to paragraphize it
                if isinstance(node, types.InternalNode):
                    node = _paragraphize(node)
                node_with_paragraphs.add_child(node)

    return node_with_paragraphs


def parse(latex: str, path: typing.Optional[typing.Union[str, pathlib.Path]] = None):
    """Parses a LaTeX string into a problem tree."""
    soup = TexSoup.TexSoup(latex)

    if path is not None:
        path = pathlib.Path(path)

    context = _Context(path)

    tree = _convert_soup_node(soup, context)
    return _paragraphize(tree)
