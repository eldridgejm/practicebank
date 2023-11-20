import argparse
import pathlib
import sys
import rich


from .api import build, tags, tagless, insert, renumber
from . import exceptions


# build subcommand =====================================================================


def _setup_build_parser(subparsers):
    subparser = subparsers.add_parser(
        "build",
        help="Build a practicebank website from a directory of practice problems.",
    )

    subparser.add_argument(
        "input",
        type=pathlib.Path,
        help="The directory containing the practice problems.",
    )
    subparser.add_argument(
        "output",
        type=pathlib.Path,
        help="The directory to which the practicebank website will be written.",
    )
    subparser.add_argument(
        "--template",
        type=pathlib.Path,
        help="A template file to use for rendering the website.",
    )

    subparser.set_defaults(command=_build)


def _build(args):
    if args.template is not None:
        with args.template.open() as f:
            template = f.read()
    else:
        template = None

    try:
        rich.print("[bold]Building practicebank website...[/bold]")
        build(args.input, args.output, template=template)
        rich.print("[bold green]Done![/bold green]")
    except exceptions.Error as exc:
        rich.print(f"[bold red]Error:[/bold red] {exc}")
        sys.exit(1)


# tags subcommand =====================================================================


def _setup_tags_parser(subparsers):
    subparser = subparsers.add_parser(
        "tags",
        help="List all tags in a practicebank.",
    )

    subparser.add_argument(
        "--input",
        type=pathlib.Path,
        help="The directory containing the practice problems.",
        default=pathlib.Path("."),
    )

    subparser.set_defaults(command=_tags)


def _tags(args):
    try:
        for tag in tags(args.input):
            print(tag)
    except exceptions.Error as exc:
        rich.print(f"[bold red]Error:[/bold red] {exc}", file=sys.stderr)
        sys.exit(1)


# tagless subcommand =====================================================================


def _setup_tagless_parser(subparsers):
    subparser = subparsers.add_parser(
        "tagless",
        help="List all problems that do not have any tags.",
    )

    subparser.add_argument(
        "--input",
        type=pathlib.Path,
        help="The directory containing the practice problems.",
        default=pathlib.Path("."),
    )

    subparser.set_defaults(command=_tagless)


def _tagless(args):
    try:
        for problem in tagless(args.input):
            print(problem)
    except exceptions.Error as exc:
        rich.print(f"[bold red]Error:[/bold red] {exc}", file=sys.stderr)
        sys.exit(1)


# insert subcommand =====================================================================


def _setup_insert_parser(subparsers):
    subparser = subparsers.add_parser(
        "insert",
        help="Insert a problem into a practicebank.",
    )

    subparser.add_argument(
        "--path_to_pb",
        type=pathlib.Path,
        default=pathlib.Path("."),
        help="The path to the practicebank.",
    )
    subparser.add_argument(
        "path_to_problems",
        type=pathlib.Path,
        nargs="+",
        help="The path(s) to the problem(s) to insert.",
    )

    subparser.set_defaults(command=_insert)


def _insert(args):
    try:
        for new_problem_path in args.path_to_problems:
            insert(args.path_to_pb, new_problem_path)
    except exceptions.Error as exc:
        rich.print(f"[bold red]Error:[/bold red] {exc}", file=sys.stderr)
        sys.exit(1)


# renumber subcommand =====================================================================


def _setup_renumber_parser(subparsers):
    subparser = subparsers.add_parser(
        "renumber",
        help="Renumber problems in a practicebank.",
    )

    subparser.add_argument(
        "--path_to_pb",
        type=pathlib.Path,
        default=pathlib.Path("."),
        help="The path to the practicebank.",
    )

    subparser.set_defaults(command=_renumber)


def _renumber(args):

    def callback(old, new):
        rich.print(f"[bold]Renumbering {old} -> {new}[/bold]")

    try:
        renumber(args.path_to_pb, callback=callback)
    except exceptions.Error as exc:
        rich.print(f"[bold red]Error:[/bold red] {exc}", file=sys.stderr)
        sys.exit(1)


# main() ===============================================================================


def main():
    """Main entry point for the practicebank CLI.

    There are multiple subcommands:

        - build
        - insert
        - renumber
        - tags
        - tagless

    """
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers()

    _setup_build_parser(subparsers)
    _setup_insert_parser(subparsers)
    _setup_renumber_parser(subparsers)
    _setup_tags_parser(subparsers)
    _setup_tagless_parser(subparsers)

    args = parser.parse_args()
    if hasattr(args, "command"):
        args.command(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
