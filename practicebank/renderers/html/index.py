"""Generates an index of practice problems from a directory."""

import pathlib
import textwrap
import collections

import typing

from ... import types
from .problem import render


DEFAULT_TEMPLATE = textwrap.dedent(
    """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Practice Problems</title>
        <link rel="stylesheet" href="{path_to_root}style.css">

        <script type="text/x-mathjax-config">
          MathJax.Hub.Config({{
            tex: {{
              inlineMath: [ ['$$','$$'], ["\\(","\\)"] ],
              displayMath: [             // start/end delimiter pairs for display math
                  ['\\[', '\\]']
              ],
              processEscapes: true
            }}
          }});
        </script>

        <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
        <script type="text/javascript" id="MathJax-script" async
          src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js">
        </script>
    </head>
    <body>
        {body}
    </body>
    </html>
""".strip()
)


def _format_tag(tag: str) -> str:
    """Formats tag name as a valid filename.

    Replaces spaces with hyphens, and converts to lowercase.

    """
    return tag.lower().replace(" ", "-")


def _write_images(problem: types.Problem, directory: pathlib.Path):
    """Writes images for a problem to a directory.

    Parameters
    ----------
    problem : Problem
        The problem to write images for.
    directory : Path
        The images directory. Images for the problem will be placed in
        <directory>/<problem.id/

    """
    queue = collections.deque([problem])
    id = problem.metadata.id

    while queue:
        node = queue.popleft()
        if isinstance(node, types.Image):
            (directory / id).mkdir(parents=True, exist_ok=True)
            with (directory / id / node.relative_path).open("wb") as f:
                f.write(node.data)

        if isinstance(node, types.InternalNode):
            for child in node.children():
                queue.append(child)


def _fix_image_paths(problem: types.Problem, path_to_image_directory: str):
    """Fixes image paths by prepending path to root.

    Parameters
    ----------
    problem : Problem
        The problem to fix image paths for.
    path_to_image_directory : str
        The path to the directory containing images. This path will be
        prepended to all image paths.

    This function modifies the problem in-place.

    """
    queue = collections.deque([problem])
    id = problem.metadata.id

    while queue:
        node = queue.popleft()
        if isinstance(node, types.Image):
            node.relative_path = (
                path_to_image_directory + f"/{id}/" + node.relative_path
            )

        if isinstance(node, types.InternalNode):
            for child in node.children():
                queue.append(child)


def _generate_tag_index(
    problems: typing.List[types.Problem],
    directory: pathlib.Path,
    tag: str,
    template=DEFAULT_TEMPLATE,
):
    """Generates tag indices under <directory>/tags."""
    problems_with_tag = [p.deep_copy() for p in problems if tag in p.metadata.tags]

    for problem in problems_with_tag:
        _fix_image_paths(problem, path_to_image_directory="../images/")

    html = '<h1>Practice Problems Tagged: "{}"</h1>'.format(tag)
    html += "<p>Go back to <a href='../index.html'>practice problems index</a>.</p>"
    html += "\n".join(render(p) for p in problems_with_tag)
    html = template.format(body=html, path_to_root="../")
    with open(directory / "tags" / f"{_format_tag(tag)}.html", "w") as f:
        f.write(html)


def _generate_all_problems_index(
    problems: typing.List[types.Problem],
    directory: pathlib.Path,
    template=DEFAULT_TEMPLATE,
):
    # generate index of all problems
    html = "<h1>All Practice Problems</h1>"
    html += "<p>Go back to <a href='index.html'>practice problems index</a>.</p>"
    html += "\n".join(render(p) for p in problems)
    html = template.format(body=html, path_to_root="")

    with open(directory / "all.html", "w") as f:
        f.write(html)


def _generate_untagged_problems_index(
    problems: typing.List[types.Problem],
    directory: pathlib.Path,
    template=DEFAULT_TEMPLATE,
):
    # generate index of untagged problems, if there are any
    untagged_problems = [p for p in problems if not p.metadata.tags]
    if untagged_problems:
        html = "<h1>Untagged Practice Problems</h1>"
        html += "\n".join(render(p) for p in untagged_problems)
        html = template.format(body=html, path_to_root="")
        with open(directory / "untagged.html", "w") as f:
            f.write(html)


def _generate_main_page(
    directory: pathlib.Path, tags: typing.Collection[str], template=DEFAULT_TEMPLATE
):
    # generate index
    html = "<h1>Practice Problems</h1>"
    html += "<h2>By Tag</h2>"
    html += '<ul class="tag-index">'
    for tag in sorted(tags):
        html += f'<li><a href="tags/{_format_tag(tag)}.html">{tag}</a></li>'
    html += "</ul>"
    html += textwrap.dedent(
        """
        <p>
            Or see a list of <a href="all.html">all problems</a>.
        </p>
    """
    )

    html = template.format(body=html, path_to_root="")
    with open(directory / "index.html", "w") as f:
        f.write(html)


def generate(
    problems: typing.Sequence[types.Problem], directory: pathlib.Path, template=None
):
    """Produces an HTML index for a bank of practice problems.

    Parameters
    ----------

    problems : Sequence[Problem]
        A sequence of problems to build an index for.

    directory : Path
        The directory to which the index will be written.

    template : str, optional
        A template to use for the index. The template should contain two placeholders:
        {body} and {path_to_root}. {body} will be replaced with the page's contents, and
        {path_to_root} will be replaced with the path to the root of the problem
        bank.

    """

    if template is None:
        template = DEFAULT_TEMPLATE

    for problem in problems:
        _write_images(problem, directory / "images")

    all_tags = set()
    for problem in problems:
        all_tags.update(problem.metadata.tags)

    # generate tag index pages
    (directory / "tags").mkdir()
    for tag in all_tags:
        _generate_tag_index(problems, directory, tag, template=template)

    # point all image paths to the "images/" directory
    for problem in problems:
        _fix_image_paths(problem, path_to_image_directory="images/")

    _generate_all_problems_index(problems, directory, template=template)
    _generate_untagged_problems_index(problems, directory, template=template)
    _generate_main_page(directory, all_tags, template=template)
