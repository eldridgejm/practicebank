from .. import io
import pathlib
import shutil
import typing


def renumber(path_to_pb: pathlib.Path, callback: typing.Optional[typing.Callable[[str, str], None]] = None):
    """Renumbers the problems in a practice bank so that they are contiguous.

    Ensures that all problem identifiers have the proper amount of zero padding
    necessary for the number of problems in the bank. Keeps the order of the
    problems the same.

    Parameters
    ----------
    path_to_pb : pathlib.Path
        The path to the practice bank to renumber.
    callback : Callable[[str, str], None], optional
        A callback function that is called with the old and new identifiers
        after each problem is renumbered. Useful for logging.

    """
    pb = io.load(path_to_pb)
    n = len(pb.problems)

    def _new_identifier(i):
        return str(i).zfill(len(str(n)))

    for i, problem in enumerate(pb.problems):
        new_identifier = _new_identifier(i + 1)
        if not (path_to_pb / new_identifier).exists():
            shutil.move(
                path_to_pb / problem.identifier, path_to_pb / new_identifier
            )
            if callback is not None:
                callback(problem.identifier, new_identifier)
