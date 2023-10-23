import argparse
import itertools
import pathlib
import sys

import yaml

from .parsers.latex import parse
from .renderers.html.index import generate
from . import types


def _read_problem(problem_dir: pathlib.Path):
    with open(problem_dir / "problem.tex") as f:
        contents = f.read()

    # the first few lines of the file, starting with %%, are YAML metadata;
    # the rest is the LaTeX source
    lines = list(contents.splitlines())

    if not lines:
        raise ValueError(f"Problem {problem_dir} is empty")

    yaml_lines = []
    for i, line in enumerate(lines):
        if line.startswith("%%"):
            yaml_lines.append(line)
        else:
            break

    latex_lines = lines[i:]

    metadata = yaml.load(
        "\n".join(line[2:].strip() for line in yaml_lines), Loader=yaml.Loader
    )

    if metadata is None:
        metadata = {}

    latex = "\n".join(latex_lines)
    node = parse(latex, problem_dir)

    if not isinstance(node, types.Problem):
        raise TypeError(f"Expected Problem, got {type(node)}")

    node.metadata = types.ProblemMetadata(
        id=problem_dir.name, tags=metadata.get("tags", [])
    )

    return node


def _read_problems(directory: pathlib.Path) -> list[types.InternalNode]:
    """Reads the practice problems from a directory."""

    def is_valid_directory(p):
        return p.is_dir() and not p.name.startswith(".") and not p.name.startswith("_")

    problem_dirs = (d for d in sorted(directory.iterdir()) if is_valid_directory(d))

    return [_read_problem(d) for d in problem_dirs]


def main():
    """Builds a website practicebank from a directory of practice problems."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "input",
        type=pathlib.Path,
        help="The directory containing the practice problems.",
    )
    parser.add_argument(
        "output",
        type=pathlib.Path,
        help="The directory to which the practicebank website will be written.",
    )
    parser.add_argument(
        "--template",
        type=pathlib.Path,
        default=None,
        help=(
            "The template to use for the index."
            " If not specified, the default template will be used."
        ),
    )

    args = parser.parse_args()

    if args.template is not None:
        with open(args.template) as f:
            template = f.read()
    else:
        template = None

    if args.output.exists():
        sys.exit(f"Error: Output directory {args.output} already exists.")

    args.output.mkdir(parents=True)

    problems = _read_problems(args.input)
    generate(problems, args.output, template=template)


if __name__ == "__main__":
    main()
