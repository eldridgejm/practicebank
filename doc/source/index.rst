.. practicebank documentation master file, created by
   sphinx-quickstart on Wed Nov 15 22:52:09 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

practicebank
============

`practicebank` is a static site generator that builds websites from a
collection of practice problems. Problems can be written in two formats: LaTeX
using `DSCTeX <https://eldridgejm.github.io/dsctex>`_, or in
Gradescope-flavored markdown. `practicebank` is built on top of `panprob
<https://eldridgejm.github.io/panprob/>`_.

Usage
-----

To build a website from a bank of practice problems, use the `build` subcommand, like so:

.. code:: bash

   practicebank build <path_to_practice_bank> <output_directory> --template <path_to_template>

The template file is optional. If provided, it should be in the form of a
Python format string containing the following fields:

- :code:`{title}`: The title of the page.
- :code:`{relative_path_to_root}`: The relative path to the root of the website.
- :code:`{body}`: The content of the page.

Embedding in another site
~~~~~~~~~~~~~~~~~~~~~~~~~

By default, each page is a standalone HTML document that loads MathJax and
highlight.js itself. To embed the pages in a site that wraps them in its own
theme, pass :code:`--fragment` instead of :code:`--template`:

.. code:: bash

   practicebank build <path_to_practice_bank> <output_directory> --fragment

Each page is then written as an HTML fragment without :code:`<html>`,
:code:`<head>` or :code:`<body>`, and without loading MathJax or highlight.js.
The host site should provide both. The output is designed to work with their
default configurations:

- Inline math is delimited by :code:`\(...\)` and display math by
  :code:`\[...\]`.
- Code blocks are written as :code:`<pre class="code"><code
  class="language-python">...</code></pre>`, with the problem's language.

Pages that contain problems include a small :code:`<style>` block, scoped to
practicebank's classes, that places each multiple-choice option on the same
line as its radio button or checkbox.
When badges are configured (see `Badges`_), they also include the badge
filter's own :code:`<style>` and :code:`<script>`, so the filter works in the
host's pages without anything from the host.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

Creating Practice Banks
-----------------------

To use `practicebank`, you must first create a bank of practice problems.
Formally, a practice bank is a directory containing a `practicebank.yaml`
configuration file, and a collection of problem subdirectories. Each problem
subdirectory must be a number, and the subdirectory must contain either
:code:`problem.md` or :code:`problem.tex` (but not both).

An example directory structure of a practice bank is shown below:

.. code:: bash

    ├── 01/
    │   ├── image.png
    │   └── problem.md
    ├── 02/
    │   ├── code.py
    │   └── problem.tex
    ├── 03/
    │   ├── code.py
    │   └── problem.tex
    └── practicebank.yaml

The problem files themselves may contain metadata in the form of a YAML
frontmatter block. For markdown problems, this frontmatter consists of a line
of three dashes, followed by a YAML block, followed by another line of three
dashes. For LaTeX problems, the frontmatter consists of all lines at the top of
the file that begin with :code:`%%`. The YAML frontmatter may contain two
fields: :code:`tags` and :code:`source`. The :code:`tags` field is a list of
strings, and the :code:`source` field is a string that describes the origin of
the problem. For example, the frontmatter for a markdown problem might look
like:

.. code:: yaml

    ---
    tags:
      - "algebra"
      - "geometry"
    source: "2023-wi-midterm_01"
    ---

The frontmatter for a LaTeX problem might look like:

.. code:: latex

    %% tags: ["algebra", "geometry"]
    %% source: "2023-wi-midterm_01"

Configuration
-------------

The :code:`practicebank.yaml` file may contain the following keys, all of
which are optional:

- :code:`description`: Text shown at the top of the index page.
- :code:`tagsets`: A list of problem sets, each of which gets its own page
  listing every problem with one of its tags. Each has an :code:`identifier`
  (the page's file name), a :code:`title`, a :code:`description`, and
  :code:`tags`: a list of tags, or :code:`__ALL__` for every tag.
- :code:`default_code_language`: The language given to code blocks that
  don't name one (e.g., a Markdown fence with no language), so that syntax
  highlighters that skip unlabelled blocks still highlight them.
- :code:`badges`: A list of tags to show as a symbol next to a problem's
  number instead of as tags. See below.

For example:

.. code:: yaml

    description: Practice problems for the course.
    tagsets:
      - identifier: midterm-01
        title: Midterm 01
        description: Practice for Midterm 01.
        tags: [recursion, time complexity]
    badges:
      - tag: hard
        symbol: "🌶️"
        title: "One of the hardest problems on past exams"

Badges
~~~~~~

A badge is a tag that is shown as a symbol after the problem's number, as in
"Problem #294 🌶️", rather than in the problem's list of tags. Each entry in
:code:`badges` has:

- :code:`tag`: The tag, as it appears in problems' frontmatter.
- :code:`symbol`: The text shown after the problem's number.
- :code:`title` (optional): A tooltip for the symbol, also used as its
  accessible label. Defaults to the tag.
- :code:`filter_label` (optional): The label of the badge's filter switch
  (see below), e.g. "Show only the hardest problems 🌶️". Defaults to the
  symbol followed by "only", as in "🌶️ only".

A badge's tag gets no tag page, and isn't listed on the index, on tagset pages
(even a tagset that names it, or uses :code:`__ALL__`), or with a problem's
tags. It doesn't select problems for a tagset either: a problem with a badge
appears wherever its other tags put it. Its problem's
:code:`<div class="problem-outer">` carries a :code:`data-badges` attribute
listing its badges' tags.

When badges are configured, each page that lists problems (tagset pages and
tag pages, standalone or :code:`--fragment`) has a switch at the top for each
badge, labelled with its :code:`filter_label` or, by default, its symbol, as
in "🌶️ only". The switches sit between two thin rules, in the page's own font
and colors, and each whole row is clickable. Off, the page shows every
problem; on, only the problems with that badge (turning one switch on turns
the others off). Each switch is a :code:`<button role="switch">`, so it works
from the keyboard and with screen readers; its focus ring shows only for
keyboard focus. It's plain inline JavaScript and
CSS, included in the page itself:

- The choice is kept in the browser's :code:`localStorage`, so it carries over
  to the other pages.
- :code:`?only=<tag>` in a page's URL turns the filter on when the page loads,
  overriding the stored choice. The page's URL is kept in step with the
  toggle, so it can be shared.
- When the filter hides every problem on a page, the page says so, e.g. "No
  🌶️ problems in this topic."
- Without JavaScript, the toggle is hidden and every problem is shown.


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
