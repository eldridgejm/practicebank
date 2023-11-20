import pathlib

from .. import io

def tags(input: pathlib.Path) -> list[str]:
    """List all of the tags in a practice bank."""
    pb = io.load(input)
    all_tags = set()
    for problem in pb.problems:
        all_tags.update(problem.tags)

    return sorted(all_tags)


def tagless(input: pathlib.Path) -> list[str]:
    """List all of the problems without tags in a practice bank."""
    pb = io.load(input)
    return [problem.identifier for problem in pb.problems if not problem.tags]
