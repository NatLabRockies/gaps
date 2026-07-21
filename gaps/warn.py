"""Custom Warning for GAPs"""

import logging

logger = logging.getLogger("gaps")


class gapsWarning(UserWarning):  # ruff:ignore[invalid-class-name]
    """Generic gaps Warning"""

    def __init__(self, *args, **kwargs):
        """Init exception and broadcast message to logger"""
        super().__init__(*args, **kwargs)
        if args:
            logger.warning(str(args[0]), stacklevel=2)


class gapsCollectionWarning(gapsWarning):  # ruff:ignore[invalid-class-name]
    """gaps Collection waring"""


class gapsHPCWarning(gapsWarning):  # ruff:ignore[invalid-class-name]
    """gaps HPC warning"""


class gapsDeprecationWarning(gapsWarning, DeprecationWarning):  # ruff:ignore[invalid-class-name]
    """gaps deprecation warning"""
