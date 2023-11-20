import pathlib
import shutil

from .. import io


def insert(path_to_pb: pathlib.Path, path_to_problem: pathlib.Path) -> str:
    """Inserts a problem into a practice bank.

    This finds the largest problem identifier in the practice bank and
    increments it by one, then inserts the problem into the practice bank with
    that identifier.

    It does not check to make sure that the new problem is formatted correctly.

    It infers the amount of zero padding to use for the problem identifier by
    finding the length of the longest directory name in the practice bank.

    Parameters
    ----------
    path_to_pb : pathlib.Path
        The path to the practice bank.
    path_to_problem : pathlib.Path
        The path to the problem to insert.

    Returns
    -------
    str
        The identifier of the inserted problem.

    """

    pb = io.load(path_to_pb)

    # find the largest problem number
    largest_problem_number = max(int(p.identifier) for p in pb.problems)

    # infer the amount of zero padding to use
    zero_padding = max(len(p.identifier) for p in pb.problems)

    identifier = str(largest_problem_number + 1).zfill(zero_padding)

    # copy the problem into the practice bank
    shutil.copytree(path_to_problem, path_to_pb / identifier)

    return identifier
