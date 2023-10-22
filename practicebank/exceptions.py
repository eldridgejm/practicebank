class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class IllegalChild(Error):
    """Raised when attempting to add a child node of a disallowed type to a parent node."""

    def __init__(self, parent, child):
        self.parent = parent
        self.child = child

    def __str__(self):
        return f"Cannot add child of type {type(self.child)} to {type(self.parent)}."
