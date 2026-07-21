"""Custom Exceptions and Errors for gaps"""

import logging

logger = logging.getLogger("gaps")


class gapsError(Exception):  # ruff:ignore[invalid-class-name]
    """Generic gaps Error"""

    def __init__(self, *args, **kwargs):
        """Init exception and broadcast message to logger"""
        super().__init__(*args, **kwargs)
        if args:
            logger.error(str(args[0]), stacklevel=2)


class gapsConfigError(gapsError):  # ruff:ignore[invalid-class-name]
    """gaps ConfigError"""


class gapsExecutionError(gapsError):  # ruff:ignore[invalid-class-name]
    """gaps ExecutionError"""


class gapsFileNotFoundError(gapsError, FileNotFoundError):  # ruff:ignore[invalid-class-name]
    """gaps FileNotFoundError"""


class gapsIndexError(gapsError, IndexError):  # ruff:ignore[invalid-class-name]
    """gaps IndexError"""


class gapsIOError(gapsError, IOError):  # ruff:ignore[invalid-class-name]
    """gaps IOError"""


class gapsKeyError(gapsError, KeyError):  # ruff:ignore[invalid-class-name]
    """gaps KeyError"""


class gapsRuntimeError(gapsError, RuntimeError):  # ruff:ignore[invalid-class-name]
    """gaps RuntimeError"""


class gapsTypeError(gapsError, TypeError):  # ruff:ignore[invalid-class-name]
    """gaps TypeError"""


class gapsValueError(gapsError, ValueError):  # ruff:ignore[invalid-class-name]
    """gaps ValueError"""


class gapsHPCError(gapsError):  # ruff:ignore[invalid-class-name]
    """gaps HPCError"""
