"""Renders a single problem to HTML."""

import typing

from ... import types

_Node = typing.Union[types.InternalNode, types.LeafNode]

_RENDERERS = {}

def _renderer(name: _Node):
    def decorator(fn):
        _RENDERERS[name] = fn
        return fn
    return decorator

@_renderer(types.Problem)
def _(node: types.Problem):
    contents = "\n".join(_render_node(child) for child in node.children())
    return f'<div class="problem">{contents}</div>'

@_renderer(types.NormalText)
def _(node: types.NormalText):
    return node.text

@_renderer(types.BoldText)
def _(node: types.BoldText):
    return f'<b>{node.text}</b>'

@_renderer(types.ItalicText)
def _(node: types.ItalicText):
    return f'<i>{node.text}</i>'

@_renderer(types.Code)
def _(node: types.Code):
    return f'<pre class="code">{node.code}</pre>'

@_renderer(types.InlineCode)
def _(node: types.InlineCode):
    return f'<span class="code">{node.code}</span>'

@_renderer(types.FillInTheBlank)
def _(node: types.FillInTheBlank):
    return f'<input type="text" class="fill-in-the-blank" />'

@_renderer(types.InlineMath)
def _(node: types.InlineMath):
    return f'<span class="math">${node.latex}$</span>'

@_renderer(types.DisplayMath)
def _(node: types.DisplayMath):
    return f'<div class="math">\\[{node.latex}\\]</div>'

@_renderer(types.TrueFalse)
def _(node: types.TrueFalse):
    return f'<input type="checkbox" class="true-false" />'

@_renderer(types.Solution)
def _(node: types.Solution):
    contents = "\n".join(_render_node(child) for child in node.children())
    return f'<details><summary>Solution</summary>{contents}</details>'

@_renderer(types.Subproblem)
def _(node: types.Subproblem):
    contents = "\n".join(_render_node(child) for child in node.children())
    return f'<div class="subproblem">{contents}</div>'

@_renderer(types.Image)
def _(node: types.Image):
    return f'<img src="{node.relative_path}" />'

@_renderer(types.MultipleChoices)
def _(node: types.MultipleChoices):
    contents = "\n".join(_render_node(child) for child in node.children())
    return f'<div class="multiple-choices">{contents}</div>'

@_renderer(types.MultipleSelect)
def _(node: types.MultipleSelect):
    contents = "\n".join(_render_node(child) for child in node.children())
    return f'<div class="multiple-select">{contents}</div>'

@_renderer(types.Choice)
def _(node: types.Choice):
    contents = "\n".join(_render_node(child) for child in node.children())
    return f'<div class="choice">{contents}</div>'




def _render_node(node: _Node):
    if type(node) in _RENDERERS:
        return _RENDERERS[type(node)](node)
    else:
        raise NotImplementedError(f"no renderer for {type(node)}")

def render(problem: types.Problem):
    return _render_node(problem)