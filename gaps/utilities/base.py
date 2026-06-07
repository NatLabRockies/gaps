"""GAPs base utilities"""

import os
import sys
import copy
import logging
import collections
import contextlib
from pathlib import Path


logger = logging.getLogger(__name__)


def recursively_update_dict(existing, new):
    """Update a dictionary recursively

    Parameters
    ----------
    existing : dict
        Existing dictionary to update. Dictionary is copied before
        recursive update is applied.
    new : dict
        New dictionary with data to add to `existing`.

    Returns
    -------
    dict
        Existing dictionary with data updated from new dictionary.
    """

    existing = copy.deepcopy(existing)

    for key, val in new.items():
        if isinstance(val, collections.abc.Mapping):
            existing[key] = recursively_update_dict(existing.get(key, {}), val)
        else:
            existing[key] = val
    return existing


def resolve_path(path, base_dir):
    """Resolve a file path represented by the input string.

    This function resolves the input string if it resembles a path.
    Specifically, the string will be resolved if it starts  with
    "``./``" or "``..``", or it if it contains either "``./``" or
    "``..``" somewhere in the string body. Otherwise, the string
    is returned unchanged, so this function *is* safe to call on any
    string, even ones that do not resemble a path.
    This method delegates the "resolving" logic to
    :meth:`pathlib.Path.resolve`. This means the path is made
    absolute, symlinks are resolved, and "``..``" components are
    eliminated. If the ``path`` input starts with "``./``" or
    "``..``", it is assumed to be w.r.t the config directory, *not*
    the run directory.

    Parameters
    ----------
    path : str
        Input file path.
    base_dir : path-like
        Base path to directory from which to resolve path string
        (typically current directory).

    Returns
    -------
    str
        The resolved path.
    """
    base_dir = Path(base_dir)
    normalized = path.replace("\\", "/")

    if normalized.startswith("./"):
        path = base_dir / Path(normalized[2:])
    elif normalized.startswith(".."):
        path = base_dir / Path(normalized)
    elif (
        "/./" in normalized
        or normalized.endswith("/.")
        or ("/../" in normalized or normalized.endswith("/.."))
    ):
        path = Path(normalized)

    with contextlib.suppress(AttributeError):
        path = path.expanduser().resolve().as_posix()

    return path


def _is_sphinx_build():
    """``True`` if sphinx is in system modules, else ``False``"""
    return "sphinx" in sys.modules
