import pathlib

import panprob

def build(input: pathlib.Path, output: pathlib.Path):
    """Builds a website of practice problems.

    Parameters
    ----------
    input : pathlib.Path
        Path to the directory containing the input problems.
    output : pathlib.Path
        Path to the directory where the website should be built. Will be created if
        it does not exist.

    """
    output.mkdir(parents=True, exist_ok=True)
