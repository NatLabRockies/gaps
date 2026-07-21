"""GAPs i/o utilities"""

import os
import contextlib

import pandas as pd

from gaps.config import load_config, ConfigType
from gaps.exceptions import gapsValueError


def parse_points_input_to_df(points, parse_sites_callable=None):
    """Parse project points input into a pandas DataFrame.

    Parameters
    ----------
    points : object
        Project point input to normalize into a DataFrame. Supported
        input types are:

        - A pre-built DataFrame, which is returned unchanged.
        - A path to a ``.csv`` file, which is loaded with
            :func:`pandas.read_csv`.
        - A path to a supported GAPs config file (``.json``, ``.yaml``,
            ``.yml``, or ``.toml``), which is loaded with
            :func:`gaps.config.load_config` and converted to a
            DataFrame.
        - A mapping defining project points, which is converted directly
            to a DataFrame.
        - A site selector such as a single integer GID, slice, list,
            tuple, or NumPy array, which is delegated to
            `parse_sites_callable`.

    parse_sites_callable : callable, optional
        Callable used to convert numeric or array-like site selectors
        into a DataFrame of project points. If omitted, the default
        implementation supports numeric and array-like selectors but
        does not support any additional arguments. This argument is only
        used if the ``points`` input is a numeric or array-like site
        selector. If the ``points`` input is a DataFrame, path,
        or mapping, this argument is ignored. By default, ``None``.

    Returns
    -------
    pandas.DataFrame
        Parsed project points.

    Raises
    ------
    gapsValueError
        Raised if ``points`` is a path with an unsupported suffix or if
        the input type cannot be converted into project points.
    """
    if isinstance(points, pd.DataFrame):
        return points

    if isinstance(points, (str, os.PathLike)):
        points = os.fspath(points).strip()
        if points.endswith(".csv"):
            return pd.read_csv(points)

        if points.endswith(tuple(ConfigType)):
            return _parse_points_mapping(load_config(points))

        msg = (
            "Project points file must be .csv, .json, .yaml, "
            f".yml, or .toml, but received: {points}"
        )
        raise gapsValueError(msg)

    if isinstance(points, dict):
        return _parse_points_mapping(points)

    try:
        return (parse_sites_callable or _parse_sites)(points)
    except Exception:  # ruff:ignore[blind-except]
        msg = f"Cannot parse project points from input of type {type(points)}"
        raise gapsValueError(msg) from None


def _parse_points_mapping(points):
    """Parse project points from a mapping input"""
    if points and all(isinstance(value, dict) for value in points.values()):
        for v in points.values():
            v["_GAPs_to_delete"] = 0
        df = pd.DataFrame.from_dict(points, orient="index")
        df.index = pd.Index(
            pd.to_numeric(df.index, errors="raise"),
            name="gid",
        )
        return df.reset_index().drop(columns="_GAPs_to_delete")

    return pd.DataFrame(points)


def _parse_sites(points):
    """Parse project points from list or slice

    Parameters
    ----------
    points : int | str | pandas.DataFrame | slice | list
        Slice specifying project points, string pointing to a project
        points csv, or a DataFrame containing the effective csv
        contents. Can also be a single integer site value.

    Returns
    -------
    df : pandas.DataFrame
        DataFrame of sites (gids) with corresponding args

    Raises
    ------
    gapsRuntimeError
        If points not flat.
    """
    try:
        points = project_points_from_container_or_slice(points)
    except TypeError as err:
        msg = (
            f"Cannot parse points data from {points}. If this input is a "
            "container, please ensure that the container is flat (no "
            "nested gid values)."
        )
        raise gapsValueError(msg) from err

    return pd.DataFrame({"gid": points})


def project_points_from_container_or_slice(project_points):
    """Parse project point input into a list of GIDs

    Parameters
    ----------
    project_points : numeric | container
        A number or container of numbers that holds GID values. If a
        mapping (e.g. dict, pd.DataFrame, etc), a "gid" must map to the
        desired values.

    Returns
    -------
    list
        A list of integer GID values.
    """
    with contextlib.suppress((KeyError, TypeError, IndexError)):
        project_points = project_points["gid"]

    with contextlib.suppress(AttributeError):
        project_points = project_points.to_numpy()

    with contextlib.suppress(AttributeError):
        project_points = _slice_to_list(project_points)

    try:
        return [int(g) for g in project_points]
    except TypeError:
        return [int(g) for g in [project_points]]


def _slice_to_list(inputs_slice):
    """Convert a slice to a list of values"""
    start = inputs_slice.start or 0
    end = inputs_slice.stop
    if end is None:
        msg = "slice must be bounded!"
        raise gapsValueError(msg)
    step = inputs_slice.step or 1
    return list(range(start, end, step))
