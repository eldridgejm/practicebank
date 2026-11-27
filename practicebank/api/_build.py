"""Builds a practice bank into a static website."""

import copy
import functools
import html
import html as html_module
import pathlib
import re
import typing
from textwrap import dedent, indent

from .. import io, exceptions
from ..types import PracticeBank, TagSet, Problem, Badge

import panprob

# setup ================================================================================

# the HTML template that is used if one is not provided. Has the placeholders:
# "title" and "body". The body placeholder is replaced with the rendered
# practice bank. Note that templates can include a third placeholder,
# {relative_path_to_root}, which is the relative path from the current page to
# the root of the website. This is useful for linking to assets like CSS files.
_DEFAULT_TEMPLATE = dedent(
    r"""
    <!DOCTYPE html>
    <html>
        <head>
            <meta charset="utf-8">
            <title>{title}</title>

            <!-- highlightjs -->
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/default.min.css">
            <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>

            <!-- and it's easy to individually load additional languages -->
            <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/go.min.js"></script>

            <script>hljs.highlightAll();</script>

            <!-- MathJax; problems use its default delimiters, \(...\) and \[...\] -->
            <script type="text/javascript" id="MathJax-script" async
              src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js">
            </script>
        </head>
        <body>
            {body}
        </body>
    </html>
    """
).strip()

# the template used when building fragments that a host site wraps in its own page.
# The host is expected to provide MathJax and syntax highlighting.
_FRAGMENT_TEMPLATE = "{body}"

# styles for practicebank's own markup. These are included in every page, so they
# apply whether the page is standalone or embedded in a host site.
_STYLES = dedent(
    """
    <style>
    .multiple-choices .choice label, .multiple-select .choice label {
        display: flex; align-items: center; gap: 0.6em; margin: 0.25em 0; cursor: pointer;
    }
    .multiple-choices .choice p, .multiple-select .choice p { margin: 0; }
    </style>
    """
).strip()

# badge filter ========================================================================

# the toggle at the top of every page that lists problems, shown when badges are
# configured. It has one button for all problems and one per badge. The choice is
# kept in localStorage, so it carries over to the other pages, and ?only=<tag> in
# the URL sets it when the page loads. The toggle starts out hidden and the script
# reveals it, so without JavaScript the page shows every problem and no toggle.
_FILTER_STYLES = dedent(
    """
    <style>
    .practicebank-filter { display: flex; flex-wrap: wrap; align-items: center; gap: 0.4em; margin: 1em 0; }
    .practicebank-filter[hidden] { display: none; }
    .practicebank-filter button {
        font: inherit; padding: 0.2em 0.8em; border: 1px solid #888; border-radius: 1em;
        background: transparent; color: inherit; cursor: pointer;
    }
    .practicebank-filter button[aria-pressed="true"] { background: #888; color: #fff; }
    .practicebank-badge { cursor: help; }
    .practicebank-problems .problem-outer.practicebank-filtered-out,
    .practicebank-empty[hidden] { display: none !important; }
    </style>
    """
).strip()

_FILTER_SCRIPT = dedent(
    r"""
    <script>
    (function () {
        var KEY = "practicebank-only";
        var filters = document.querySelectorAll(".practicebank-filter");
        var lists = document.querySelectorAll(".practicebank-problems");
        var known = {};
        filters.forEach(function (f) {
            f.querySelectorAll("button[data-only]").forEach(function (b) {
                if (b.dataset.only) { known[b.dataset.only] = true; }
            });
        });

        function valid(tag) { return tag && known[tag] ? tag : ""; }
        function load() { try { return valid(localStorage.getItem(KEY)); } catch (e) { return ""; } }
        function save(tag) {
            try {
                if (tag) { localStorage.setItem(KEY, tag); } else { localStorage.removeItem(KEY); }
            } catch (e) {}
        }

        function apply(tag) {
            filters.forEach(function (f) {
                f.hidden = false;
                f.querySelectorAll("button[data-only]").forEach(function (b) {
                    b.setAttribute("aria-pressed", String(b.dataset.only === tag));
                });
            });
            lists.forEach(function (list) {
                var shown = 0;
                list.querySelectorAll(".problem-outer").forEach(function (p) {
                    var badges = (p.dataset.badges || "").split(" ");
                    var keep = !tag || badges.indexOf(tag) !== -1;
                    p.classList.toggle("practicebank-filtered-out", !keep);
                    if (keep) { shown++; }
                });
                list.querySelectorAll(".practicebank-empty").forEach(function (e) {
                    e.hidden = !(tag && shown === 0 && e.dataset.only === tag);
                });
            });
            try {
                var url = new URL(location.href);
                if (tag) { url.searchParams.set("only", tag); } else { url.searchParams.delete("only"); }
                if (url.href !== location.href) { history.replaceState(history.state, "", url.href); }
            } catch (e) {}
        }

        filters.forEach(function (f) {
            f.addEventListener("click", function (event) {
                var b = event.target.closest("button[data-only]");
                if (!b) { return; }
                var tag = valid(b.dataset.only);
                save(tag);
                apply(tag);
            });
        });

        // ?only=<tag> wins over the stored choice, and becomes the stored choice
        var param = null;
        try { param = new URLSearchParams(location.search).get("only"); } catch (e) {}
        if (param !== null) { save(valid(param)); }
        apply(param !== null ? valid(param) : load());

        // pages that were prerendered or kept in the back/forward cache catch up
        // with a choice made on another page since
        function resync() { apply(load()); }
        window.addEventListener("storage", function (event) { if (event.key === KEY) { resync(); } });
        window.addEventListener("pageshow", function (event) { if (event.persisted) { resync(); } });
        document.addEventListener("prerenderingchange", resync);
    })();
    </script>
    """
).strip()


def _render_filter(badges: typing.Sequence[Badge]) -> str:
    """Renders the "All | 🌶️ only" toggle, or nothing if there are no badges."""
    if not badges:
        return ""
    buttons = ['<button type="button" data-only="" aria-pressed="true">All</button>']
    for badge in badges:
        label = html.escape(badge.title or badge.tag)
        buttons.append(
            f'<button type="button" data-only="{html.escape(badge.tag)}" '
            f'aria-pressed="false" title="{label}">'
            f"{html.escape(badge.symbol)} only</button>"
        )
    return (
        '<div class="practicebank-filter" role="group" aria-label="Filter problems" hidden>\n'
        + "\n".join(buttons)
        + "\n</div>"
    )


def _render_problem_list(
    pb: PracticeBank,
    problems_html: list[str],
    noun: str,
) -> str:
    """Renders the problems of a page, with the badge filter if badges are configured.

    Parameters
    ----------
    pb : PracticeBank
        The practice bank, whose config gives the badges.
    problems_html : list[str]
        The rendered problems.
    noun : str
        What the page lists, as in "No 🌶️ problems in this {noun}."

    """
    badges = pb.config.badges
    if not badges:
        return "\n".join(problems_html)

    empty = "\n".join(
        f'<p class="practicebank-empty" data-only="{html.escape(b.tag)}" hidden>'
        f"No {html.escape(b.symbol)} problems in this {noun}.</p>"
        for b in badges
    )
    return "\n".join(
        [
            _FILTER_STYLES,
            _render_filter(badges),
            '<div class="practicebank-problems">',
            *problems_html,
            empty,
            "</div>",
            _FILTER_SCRIPT,
        ]
    )


# utility functions ====================================================================


def _badge_tags(pb: PracticeBank) -> set[str]:
    """Returns the set of tags that are configured as badges."""
    return {badge.tag for badge in pb.config.badges}


def _all_tags(pb: PracticeBank) -> list[str]:
    """Returns a list of all tags in the practice bank, sorted alphabetically.

    Tags configured as badges are not included.

    """
    tags = set()
    for problem in pb.problems:
        tags.update(problem.tags)
    return sorted(tags - _badge_tags(pb))


def _tagset_tags(pb: PracticeBank, tagset: TagSet) -> list[str]:
    """Returns the tags in a tagset, sorted, without any badge tags."""
    if tagset.tags == "__ALL__":
        return _all_tags(pb)
    return sorted(set(tagset.tags) - _badge_tags(pb))


# AST posprocessors ====================================================================

# these do some post-processing of a problem's AST before it is rendered


def _add_solution_to_true_false(node: panprob.ast.Node):
    """This adds a solution to a true/false problem if it doesn't already have one."""

    return node


# parser overrides =====================================================================

# these override panprob's default DSCTeX converters for specific LaTeX environments


def _convert_minted(env, convert) -> panprob.ast.Code:
    """Converts a minted environment, which may have options before its language.

    panprob reads the language from the first argument, so in
    ``\\begin{minted}[autogobble]{python}`` it takes "autogobble" as the language. The
    language is the last argument.

    """
    return panprob.ast.Code(
        language=env.args[-1].raw_contents, code=dedent(env.raw_contents)
    )


_DSCTEX_ENVIRONMENT_CONVERTERS = {
    "minted": _convert_minted,
}


# node renderers =======================================================================

# these override panprob's default HTML renderers for specific AST node types


def _render_code_node(node: panprob.ast.Code, render_child) -> str:
    """Renders a code block in the conventional form expected by syntax highlighters.

    The language is given by a ``language-*`` class on the ``<code>`` element, and
    blank lines at the start and end of the code are removed.

    """
    code = re.sub(r"^\s*\n", "", node.code).rstrip()
    code = html.escape(code, quote=False)
    if node.language:
        code_class = f' class="language-{html.escape(node.language)}"'
    else:
        code_class = ""
    return f'<pre class="code"><code{code_class}>{code}</code></pre>'


def _render_align_math_node(node: panprob.ast.AlignMath, render_child) -> str:
    """Renders an align environment as display math delimited by \\[...\\].

    panprob delimits it with $$...$$, but \\[...\\] is display math under MathJax's
    default configuration, so the output doesn't depend on a custom MathJax config.

    """
    env = "align*" if node.starred else "align"
    return f'<div class="math">\\[\\begin{{{env}}}{node.latex}\\end{{{env}}}\\]</div>'


_NODE_RENDERER_OVERRIDES = {
    panprob.ast.Code: _render_code_node,
    panprob.ast.AlignMath: _render_align_math_node,
}


# renderers ============================================================================

# pages commonly need to render problems, a list of tags, etc. The following
# functions are used to render these things.


def _render_vertical_tag_link_list(tags: list[str], relative_path_to_root=".") -> str:
    """Renders HTML for an <ul></ul> of links to tag pages.

    Parameters
    ----------
    tags : list[str]
        The tags to include links to.
    relative_path_to_root : str, optional
        The relative path from the current page to the root of the website. This
        is used to form the links to the tag pages.

    Returns
    -------
    str
        The rendered HTML, including the outer <ul> and </ul> tags.

    """
    tags = sorted(tags)
    return (
        "<ul>\n"
        + "\n".join(
            f"<li><a href='{relative_path_to_root}/tags/{tag}.html'>{tag}</a></li>"
            for tag in tags
        )
        + "\n</ul>"
    )


def _render_inline_tag_link_list(tags, relative_path_to_root="."):
    """Renders HTML for a comma-separated list of links to tag pages.

    Parameters
    ----------
    tags : list[str]
        The tags to include links to.
    relative_path_to_root : str, optional
        The relative path from the current page to the root of the website. This
        is used to form the links to the tag pages.

    Returns
    -------
    str
        The rendered HTML.

    """
    return ", ".join(
        f"<a href='{relative_path_to_root}/tags/{tag}.html'>{tag}</a>" for tag in tags
    )


def _render_problem(
    problem: Problem,
    output: pathlib.Path,
    relative_path_to_root=".",
    badges: typing.Sequence[Badge] = (),
) -> str:
    """Renders a problem as HTML.

    Parameters
    ----------
    problem : Problem
        The problem to render.
    output : pathlib.Path
        The path to the output directory; i.e., the root of the website.
    relative_path_to_root : str, optional
        The relative path from the current page to the root of the website. This
        is used to form the links to the tag pages.
    badges : Sequence[Badge], optional
        The configured badges. A badge's tag is shown as its symbol after the
        problem's number instead of in the list of tags.

    Returns
    -------
    str
        The rendered HTML.

    """

    def transform_path(relpath: str):
        return str(
            pathlib.Path(relative_path_to_root)
            / "images"
            / problem.identifier
            / relpath
        )

    def _render_with_panprob():
        parser = {
            "gsmd": panprob.parsers.gsmd.parse,
            "dsctex": functools.partial(
                panprob.parsers.dsctex.parse,
                environment_converters=_DSCTEX_ENVIRONMENT_CONVERTERS,
            ),
        }[problem.format]

        tree = parser(problem.contents)
        tree = _add_solution_to_true_false(tree)
        tree = panprob.postprocessors.subsume_code(tree, problem.path)
        tree = panprob.postprocessors.copy_images(
            tree,
            problem.path,
            output / "images" / problem.identifier,
            transform_path=transform_path,
        )
        return panprob.renderers.html.render(
            tree, overrides=_NODE_RENDERER_OVERRIDES
        )

    try:
        html = _render_with_panprob()
    except panprob.exceptions.ParseError as exc:
        raise exceptions.ProblemError(problem.identifier, str(exc))

    own_badges = [b for b in badges if b.tag in problem.tags]
    tags = sorted(problem.tags - {b.tag for b in badges})

    heading = f"Problem #{problem.identifier}"
    for badge in own_badges:
        label = html_module.escape(badge.title or badge.tag)
        heading += (
            f' <span class="practicebank-badge" data-badge="{html_module.escape(badge.tag)}" '
            f'role="img" title="{label}" aria-label="{label}">'
            f"{html_module.escape(badge.symbol)}</span>"
        )

    if own_badges:
        badges_attr = (
            ' data-badges="' + html_module.escape(" ".join(b.tag for b in own_badges)) + '"'
        )
    else:
        badges_attr = ""

    if tags:
        tags_line = f"<p>Tags: {_render_inline_tag_link_list(tags, relative_path_to_root)}</p>"
    else:
        tags_line = ""

    return dedent(
        f"""

        <div class="problem-outer"{badges_attr}>
        <h2>{heading}</h2>
        {tags_line}
        {html}
        </div>

        """
    )


# page writers =========================================================================

# these functions write the actual HTML pages


def _write_index(
    pb: PracticeBank, output_directory: pathlib.Path, template: str = _DEFAULT_TEMPLATE
):
    """Writes index.html in the output directory.

    Parameters
    ----------
    pb : PracticeBank
        The practice bank to write the index for.
    output_directory : pathlib.Path
        The path to the output directory; i.e., the root of the website.
    template : str, optional
        The template to use for the page. Can have the following variables:
        - {body}: the body of the page
        - {title}: the title of the page
        - {relative_path_to_root}: the relative path from the current page to the
          root of the website.

    """

    def _tagset_section_html(ts: TagSet) -> str:
        tags = _tagset_tags(pb, ts)

        tags_html = _render_vertical_tag_link_list(tags, relative_path_to_root=".")

        return dedent(
            f"""
            <div class="tagset">
                <h2>{ts.title}</h2>
                <p>{ts.description}</p>
                <p>
                    <a href="./{ts.identifier}.html">See all problems in this set</a>, or
                    choose a tag below to view only those problems.
                </p>
            {{tags_html}}
            </div>
            """
        ).format(tags_html=tags_html)

    body = "\n".join(
        [
            "<div>",
            "<h1>Practice Problems</h1>",
            "<p>" + pb.config.description + "</p>" if pb.config.description else "",
            *[_tagset_section_html(ts) for ts in pb.config.tagsets.values()],
            "</div>",
        ]
    )

    html = template.format(
        title="Practice Problems",
        body=body,
        relative_path_to_root=".",
    )

    with (output_directory / "index.html").open("w") as f:
        f.write(html)


def _write_tagset_page(
    pb: PracticeBank,
    tagset: TagSet,
    output: pathlib.Path,
    template: str = _DEFAULT_TEMPLATE,
):
    """Writes a tagset page in the output directory.

    Parameters
    ----------
    pb : PracticeBank
        The practice bank to write the index for.
    tagset : TagSet
        The tagset to write the page for.
    output : pathlib.Path
        The path to the output directory; i.e., the root of the website.
    template : str, optional
        The template to use for the page. Can have the following variables:
        - {body}: the body of the page
        - {title}: the title of the page
        - {relative_path_to_root}: the relative path from the current page to the
          root of the website.

    """
    tags = _tagset_tags(pb, tagset)

    body = dedent(
        f"""
        {{styles}}
        <h1>{tagset.title}</h1>
        <p>{tagset.description}</p>
        <p>Tags in this problem set:</p>
        <ul>
        {{tags_html}}
        </ul>

        {{problems_html}}
        """
    ).format(
        styles=_STYLES,
        tags_html=_render_vertical_tag_link_list(tags),
        problems_html=_render_problem_list(
            pb,
            [
                _render_problem(problem, output, badges=pb.config.badges)
                for problem in pb.problems
                if problem.tags.intersection(tags) or tagset.tags == "__ALL__"
            ],
            noun="set",
        ),
    )

    html = template.format(title=tagset.title, body=body, relative_path_to_root=".")

    with (output / f"{tagset.identifier}.html").open("w") as f:
        f.write(html)


def _write_tag_page(
    pb: PracticeBank, tag: str, output: pathlib.Path, template: str = _DEFAULT_TEMPLATE
):
    """Writes the page for a single tag in the tags/ directory.

    Parameters
    ----------
    pb : PracticeBank
        The practice bank to write the index for.
    tag : str
        The tag to write the page for.
    output : pathlib.Path
        The path to the output directory; i.e., the root of the website.
    template : str, optional
        The template to use for the page. Can have the following variables:
        - {body}: the body of the page
        - {title}: the title of the page
        - {relative_path_to_root}: the relative path from the current page to the
          root of the website.

    """
    (output / "tags").mkdir(exist_ok=True)

    body = dedent(
        f"""
        {{styles}}
        <h1>Problems tagged with "{tag}"</h1>
        {{problems_html}}
        """
    ).format(
        styles=_STYLES,
        problems_html=_render_problem_list(
            pb,
            [
                _render_problem(
                    problem, output, relative_path_to_root="..", badges=pb.config.badges
                )
                for problem in pb.problems
                if tag in problem.tags
            ],
            noun="topic",
        ),
    )

    html = template.format(
        title=f"Problems tagged with {tag}", body=body, relative_path_to_root=".."
    )

    with (output / f"tags/{tag}.html").open("w") as f:
        f.write(html)


# build() ==============================================================================


def build(
    input: pathlib.Path,
    output: pathlib.Path,
    template: typing.Optional[str] = None,
    fragment: bool = False,
):
    """Builds a website of practice problems.

    Parameters
    ----------
    input : pathlib.Path
        Path to the directory containing the practice bank.
    output : pathlib.Path
        Path to the directory where the website should be built. Will be created if
        it does not exist.
    template : str, optional
        A template string used to render HTML pages. Can contain the following
        placeholders:

        - ``{title}``: The title of the page.
        - ``{body}``: The body of the page.
        - ``{relative_path_to_root}``: The relative path from the page to the output
            directory root.

    fragment : bool, optional
        If True, each page is written as an HTML fragment meant to be wrapped by a
        host site: there is no ``<html>``, ``<head>`` or ``<body>``, and MathJax and
        highlight.js are not loaded, since the host is expected to provide them.
        Cannot be used together with ``template``. Default: False.

    """
    if fragment and template is not None:
        raise ValueError("Cannot provide a template when building fragments.")

    if fragment:
        template = _FRAGMENT_TEMPLATE
    elif template is None:
        template = _DEFAULT_TEMPLATE

    output.mkdir(parents=True, exist_ok=True)

    practice_bank = io.load(input, raise_on_error=True)

    _write_index(practice_bank, output, template=template)

    for tagset in practice_bank.config.tagsets.values():
        _write_tagset_page(practice_bank, tagset, output, template=template)

    for tag in _all_tags(practice_bank):
        _write_tag_page(practice_bank, tag, output, template=template)
