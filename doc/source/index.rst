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


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
