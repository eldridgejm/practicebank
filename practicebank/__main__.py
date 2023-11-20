import argparse
import pathlib


from ._build import build


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

    args = parser.parse_args()

    build(args.input, args.output)
