import argparse
import pathlib
import sys
import rich


from ._build import build
from . import exceptions


if __name__ == "__main__":
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
        help="A template file to use for rendering the website.",
    )

    args = parser.parse_args()

    if args.template is not None:
        with args.template.open() as f:
            template = f.read()
    else:
        template = None

    try:
        build(args.input, args.output, template=template)
    except exceptions.Error as exc:
        rich.print(f"[bold red]Error:[/bold red] {exc}")
        sys.exit(1)
