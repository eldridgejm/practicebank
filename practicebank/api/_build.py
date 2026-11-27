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
        display: flex; align-items: baseline; gap: 0.6em; margin: 0.25em 0; cursor: pointer;
    }
    /* level the box with the first line of the choice, not the middle of a wrapped one */
    .multiple-choices .choice input, .multiple-select .choice input { flex: none; margin: 0; }
    .multiple-choices .choice p, .multiple-select .choice p { margin: 0; }
    </style>
    """
).strip()

# badge filter ========================================================================

# the switch at the top of every page that lists problems, shown when badges are
# configured: one per badge, off for all problems and on for only that badge's
# problems (at most one is on at a time). The choice is
# kept in localStorage, so it carries over to the other pages, and ?only=<tag> in
# the URL sets it when the page loads. The toggle starts out hidden and the script
# reveals it, so without JavaScript the page shows every problem and no toggle.
_FILTER_STYLES = dedent(
    """
    <style>
    .practicebank-filter {
        display: flex; flex-direction: column; gap: 0.25em;
        margin: 1.5em 0; padding: 0.6em 0;
        border-top: 1px solid rgba(128, 128, 128, 0.3);
        border-bottom: 1px solid rgba(128, 128, 128, 0.3);
    }
    .practicebank-filter[hidden] { display: none; }
    .practicebank-filter button[role="switch"] {
        -webkit-appearance: none; appearance: none;
        display: flex; align-items: center; gap: 0.75em; width: 100%;
        margin: 0; padding: 0.35em 0.25em; border: 0; border-radius: 6px;
        background: none; box-shadow: none; color: inherit;
        font: inherit; line-height: inherit; text-align: left; cursor: pointer;
    }
    .practicebank-filter button[role="switch"]:focus { outline: none; }
    .practicebank-filter button[role="switch"]:focus-visible:not([data-pointer]) {
        outline: 2px solid #3b82f6; outline-offset: 2px;
    }
    .practicebank-switch {
        position: relative; flex: none; width: 44px; height: 24px; border-radius: 12px;
        background: #9ca3af; transition: background-color 0.2s ease;
    }
    .practicebank-switch::after {
        content: ""; position: absolute; top: 2px; left: 2px;
        width: 20px; height: 20px; border-radius: 50%; background: #fff;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.3); transition: transform 0.2s ease;
        will-change: transform;
    }
    button[aria-checked="true"] > .practicebank-switch { background: #dc2626; }
    button[aria-checked="true"] > .practicebank-switch::after { transform: translateX(20px); }
    @media (prefers-reduced-motion: reduce) {
        .practicebank-switch, .practicebank-switch::after { transition: none; }
    }
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

        function setSwitches(tag) {
            filters.forEach(function (f) {
                f.hidden = false;
                f.querySelectorAll("button[data-only]").forEach(function (b) {
                    b.setAttribute("aria-checked", String(b.dataset.only === tag));
                });
            });
        }

        function filterProblems(tag) {
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

        // apply a choice at once: on page load, and when another page changes it
        var pending = null;
        function apply(tag) {
            clearTimeout(pending);
            pending = null;
            latest++;
            setSwitches(tag);
            filterProblems(tag);
        }

        // on a toggle, move the switch first and filter after its slide: showing or
        // hiding many problems is a long relayout (a quarter second on a page with a
        // couple hundred problems and their math), which would freeze the slide if it
        // ran in the same frame. Toggling again before then replaces the pending
        // filter, so only the last choice is applied.
        // With reduced motion the switch doesn't slide, so it only has to be painted
        // first: the filter runs in a task after the next frame.
        var SLIDE_MS = 220;  // just over the switch's 0.2s transition
        var latest = 0;
        function toggle(tag) {
            setSwitches(tag);
            clearTimeout(pending);
            var id = ++latest;
            function run() {
                if (id !== latest) { return; }
                pending = null;
                filterProblems(tag);
            }
            var reduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
            if (reduce) {
                requestAnimationFrame(function () {
                    if (id === latest) { pending = setTimeout(run, 0); }
                });
            } else {
                pending = setTimeout(run, SLIDE_MS);
            }
        }

        // show the focus ring only for keyboard focus: some browsers count a click on a
        // button as focus-visible, so a switch clicked with the pointer is marked
        // until it is next used from the keyboard or loses focus
        filters.forEach(function (f) {
            f.addEventListener("pointerdown", function (event) {
                var b = event.target.closest("button[data-only]");
                if (b) { b.setAttribute("data-pointer", ""); }
            });
            f.addEventListener("keydown", function (event) {
                var b = event.target.closest("button[data-only]");
                if (b) { b.removeAttribute("data-pointer"); }
            });
            f.addEventListener("focusout", function (event) {
                var b = event.target.closest("button[data-only]");
                if (b) { b.removeAttribute("data-pointer"); }
            });
        });

        filters.forEach(function (f) {
            f.addEventListener("click", function (event) {
                var b = event.target.closest("button[data-only]");
                if (!b) { return; }
                // a switch that is on turns the filter off; one that is off turns it on
                var on = b.getAttribute("aria-checked") === "true";
                var tag = on ? "" : valid(b.dataset.only);
                save(tag);
                toggle(tag);
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
    """Renders a switch per badge, or nothing if there are no badges.

    Each switch is labelled with its badge's ``filter_label``, or "<symbol> only".

    """
    if not badges:
        return ""
    switches = []
    for badge in badges:
        title = html.escape(badge.title or badge.tag)
        label = badge.filter_label or f"{badge.symbol} only"
        switches.append(
            f'<button type="button" role="switch" aria-checked="false" '
            f'data-only="{html.escape(badge.tag)}" title="{title}">'
            '<span class="practicebank-switch" aria-hidden="true"></span>'
            f'<span class="practicebank-switch-label">{html.escape(label)}</span>'
            "</button>"
        )
    return (
        '<div class="practicebank-filter" role="group" aria-label="Filter problems" hidden>\n'
        + "\n".join(switches)
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


def _render_code_node(
    node: panprob.ast.Code, render_child, default_language: typing.Optional[str] = None
) -> str:
    """Renders a code block in the conventional form expected by syntax highlighters.

    The language is given by a ``language-*`` class on the ``<code>`` element, and
    blank lines at the start and end of the code are removed. A block that doesn't
    name a language (e.g., a Markdown fence with no info string) is given
    ``default_language``, the config's ``default_code_language``, if one is set, so
    that highlighters configured to skip blocks without a ``language-*`` class still
    highlight it. Otherwise it gets no class.

    """
    code = re.sub(r"^\s*\n", "", node.code).rstrip()
    code = html.escape(code, quote=False)
    language = node.language or default_language
    if language:
        code_class = f' class="language-{html.escape(language)}"'
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


def _node_renderer_overrides(default_code_language: typing.Optional[str] = None) -> dict:
    """The renderers that replace panprob's for some nodes."""
    return {
        panprob.ast.Code: functools.partial(
            _render_code_node, default_language=default_code_language
        ),
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
    default_code_language : Optional[str], optional
        The language given to code blocks that don't name one. If None, they are
        given no language.

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
    default_code_language: typing.Optional[str] = None,
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
            tree, overrides=_node_renderer_overrides(default_code_language)
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
                _render_problem(
                    problem,
                    output,
                    badges=pb.config.badges,
                    default_code_language=pb.config.default_code_language,
                )
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
                    problem,
                    output,
                    relative_path_to_root="..",
                    badges=pb.config.badges,
                    default_code_language=pb.config.default_code_language,
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
