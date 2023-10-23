"""Renders a single problem to HTML."""

import typing
from textwrap import dedent

from ... import types


_RENDERERS = {}


def _renderer(nodetype):
    def decorator(fn):
        _RENDERERS[nodetype] = fn
        return fn

    return decorator


@_renderer(types.Problem)
def _(node: types.Problem):
    html = dedent(
        """
        <div class="problem">
            {metadata}
            <div class="problem-body">
                {contents}
            </div>
        </div>
        """.strip()
    )

    if node.metadata is not None:
        metadata = dedent(
            f"""
            <h2 class="problem-id">Problem {node.metadata.id}</h2>
            """.strip()
        )

        if node.metadata.tags:
            metadata += "<div class=\"problem-tags\">"
            metadata += "tags: " + ", ".join(node.metadata.tags)
            metadata += "</div>"

    else:
        metadata = ""

    subprob_counter = 1
    rendered_children = []
    for child in node.children():
        if isinstance(child, types.Subproblem):
            rendered_children.append(_render_subproblem(child, subprob_counter))
            subprob_counter += 1
        else:
            rendered_children.append(_render_node(child))

    contents = "\n".join(rendered_children)
    return html.format(metadata=metadata, contents=contents)


def _render_subproblem(node: types.Subproblem, counter: int):
    html = dedent(
        """
        <div class="subproblem">
            <h3 class="subproblem-id">Part {counter})</h3>
            {contents}
        </div>
        """.strip()
    )
    contents = "\n".join(_render_node(child) for child in node.children())
    return html.format(counter=counter, contents=contents)


@_renderer(types.NormalText)
def _(node: types.NormalText):
    return node.text


@_renderer(types.BoldText)
def _(node: types.BoldText):
    return f"<b>{node.text}</b>"


@_renderer(types.ItalicText)
def _(node: types.ItalicText):
    return f"<i>{node.text}</i>"


@_renderer(types.Code)
def _(node: types.Code):
    return f'<pre class="code"><code>{node.code}</code></pre>'


@_renderer(types.InlineCode)
def _(node: types.InlineCode):
    return f'<span class="inline-code"><code>{node.code}</code></span>'


@_renderer(types.InlineMath)
def _(node: types.InlineMath):
    return f'<span class="math">\\({node.latex}\\)</span>'


@_renderer(types.DisplayMath)
def _(node: types.DisplayMath):
    return f'<div class="math">\\[{node.latex}\\]</div>'


@_renderer(types.TrueFalse)
def _(node: types.TrueFalse):
    return dedent(
        """
        <div class="true-false">
            <input type="radio" name="true-false" value="true" /> True
            <input type="radio" name="true-false" value="false" /> False
        </div>
    """
    )


@_renderer(types.Solution)
def _(node: types.Solution):
    contents = "\n".join(_render_node(child) for child in node.children())
    return f"<details><summary>Solution</summary>{contents}</details>"


@_renderer(types.Image)
def _(node: types.Image):
    return (
        f'<center><div class="image"><img src="{node.relative_path}" /></div></center>'
    )


def _render_choice(node: types.Choice, kind: str):
    contents = "\n".join(_render_node(child) for child in node.children())
    # return f'<div class="choice"><input type="{kind}" />{contents}</div>'
    # place the checkbox/radio on the same line as the contents
    return f'<div class="choice"><label><input name="choice" class="choice" type="{kind}" />{contents}</label></div>'


@_renderer(types.MultipleChoices)
def _(node: types.MultipleChoices):
    # radio buttons
    contents = "\n".join(_render_choice(child, "radio") for child in node.children())
    return f'<div class="multiple-choices"><form>{contents}</form></div>'


@_renderer(types.MultipleSelect)
def _(node: types.MultipleSelect):
    contents = "\n".join(_render_choice(child, "checkbox") for child in node.children())
    return f'<div class="multiple-select">{contents}</div>'


@_renderer(types.Paragraph)
def _(node: types.Paragraph):
    contents = "".join(_render_node(child) for child in node.children())
    return f"<p>{contents}</p>"


_Node = typing.Union[types.InternalNode, types.LeafNode]


def _render_node(node: _Node):
    if type(node) in _RENDERERS:
        return _RENDERERS[type(node)](node)
    else:
        raise NotImplementedError(f"no renderer for {type(node)}")


def render(problem: types.Problem):
    return _render_node(problem)
