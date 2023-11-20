class Error(Exception):
    """Base class for exceptions in this module."""


class ConfigError(Error):
    """Raised when there is a problem with the configuration."""

    def __init__(self, path, message):
        self.path = path
        self.message = message

    def __str__(self):
        return f"Invalid configuration file at {self.path}. {self.message}"

class ProblemError(Error):
    """Raised when there is a problem with a problem."""

    def __init__(self, identifier, message):
        self.identifier = identifier
        self.message = message

    def __str__(self):
        return f"Problem {self.identifier} is invalid: {self.message}"
