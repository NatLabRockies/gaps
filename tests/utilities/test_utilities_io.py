"""GAPs base utilities tests"""
from pathlib import Path

import numpy as np
import pytest
import pandas as pd
from pandas.testing import assert_frame_equal

from gaps import TEST_DATA_DIR
from gaps.config import ConfigType
from gaps.exceptions import gapsValueError
from gaps.utilities.io import (
    parse_points_input_to_df,
    project_points_from_container_or_slice,
    _slice_to_list,
)


def test_parse_points_input_to_df_dataframe_passthrough():
    """Test that DataFrame inputs are returned unchanged."""
    points = pd.DataFrame({"gid": [0, 1], "config": ["a", "b"]})

    def _parse_sites(_):
        raise AssertionError("parse_sites_callable should not be used")

    assert parse_points_input_to_df(points, _parse_sites) is points


def test_parse_points_input_to_df_csv_path(points_path):
    """Test parsing project points from a CSV path string."""
    expected = pd.read_csv(points_path)

    result = parse_points_input_to_df(f"  {points_path}  ", lambda _: None)

    assert_frame_equal(result, expected)


@pytest.mark.parametrize("config_suffix", ["json", "yaml", "yml", "toml"])
def test_parse_points_input_to_df_config_path(tmp_path, config_suffix):
    """Test parsing project points from supported config files."""
    path = tmp_path / f"project_points.{config_suffix}"
    points = {
        "0": {"config": "baseline", "curtailment": 0.0},
        "5": {"config": "storm", "curtailment": 0.25},
    }
    expected = pd.DataFrame(
        {
            "gid": [0, 5],
            "config": ["baseline", "storm"],
            "curtailment": [0.0, 0.25],
        }
    )

    ConfigType(config_suffix).write(path, points)
    result = parse_points_input_to_df(path, lambda _: None)

    assert_frame_equal(result, expected)


def test_parse_points_input_to_df_nested_mapping():
    """Test parsing project points from a nested mapping."""
    points = {
        "3": {"config": "baseline", "curtailment": 0.1},
        "7": {"config": "storm", "curtailment": 0.2},
    }
    expected = pd.DataFrame(
        {
            "gid": [3, 7],
            "config": ["baseline", "storm"],
            "curtailment": [0.1, 0.2],
        }
    )

    result = parse_points_input_to_df(points, lambda _: None)

    assert_frame_equal(result, expected)


def test_parse_points_input_to_df_flat_mapping():
    """Test parsing project points from a flat mapping."""
    points = {"gid": [2, 4], "config": ["baseline", "storm"]}
    expected = pd.DataFrame(points)

    result = parse_points_input_to_df(points, lambda _: None)

    assert_frame_equal(result, expected)


@pytest.mark.parametrize(
    ("points", "comparator"),
    [
        pytest.param(9, lambda actual, expected: actual == expected, id="int"),
        pytest.param(
            slice(1, 4),
            lambda actual, expected: actual == expected,
            id="slice",
        ),
        pytest.param(
            [1, 4, 7],
            lambda actual, expected: actual == expected,
            id="list",
        ),
        pytest.param(
            (2, 5, 8),
            lambda actual, expected: actual == expected,
            id="tuple",
        ),
        pytest.param(
            np.array([3, 6, 9]),
            np.array_equal,
            id="ndarray",
        ),
    ],
)
def test_parse_points_input_to_df_site_selector(points, comparator):
    """Test delegating supported selectors to parse_sites_callable."""
    expected = pd.DataFrame({"gid": [0], "config": ["parsed"]})
    calls = []

    def _parse_sites(value):
        calls.append(value)
        return expected

    result = parse_points_input_to_df(points, _parse_sites)

    assert result is expected
    assert len(calls) == 1
    assert comparator(calls[0], points)


def test_parse_points_input_to_df_site_selector_default_callable():
    """Test parsing site selectors when parse_sites_callable is omitted."""
    result = parse_points_input_to_df(slice(1, 4))

    assert_frame_equal(result, pd.DataFrame({"gid": [1, 2, 3]}))


def test_parse_points_input_to_df_unsupported_path_suffix(tmp_path):
    """Test error raised for unsupported file suffixes."""
    path = tmp_path / "project_points.txt"
    path.write_text("gid\n0\n", encoding="utf-8")

    with pytest.raises(gapsValueError, match="Project points file must be"):
        parse_points_input_to_df(path, lambda _: None)


def test_project_points_from_container_or_slice():
    """Test the parse_project_points function"""

    base_pp = pd.read_csv(TEST_DATA_DIR / "project_points_100.csv")
    expected_gids = sorted(base_pp.gid.values)

    gids = project_points_from_container_or_slice(base_pp)
    assert gids == expected_gids

    gids = project_points_from_container_or_slice(list(range(100)))
    assert gids == expected_gids

    gids = project_points_from_container_or_slice(slice(0, 100))
    assert gids == expected_gids

    gids = project_points_from_container_or_slice(slice(None, 100, 1))
    assert gids == expected_gids

    gids = project_points_from_container_or_slice(set(range(100)))
    assert gids == expected_gids

    gids = project_points_from_container_or_slice({"gid": list(range(100))})
    assert gids == expected_gids

    with pytest.raises(gapsValueError):
        project_points_from_container_or_slice(slice(0, None))


def test_slice_to_list():
    """Test the _slice_to_list function"""
    expected_list = list(range(10))

    out_list = _slice_to_list(slice(None, 10))
    assert out_list == expected_list

    out_list = _slice_to_list(slice(None, 10, None))
    assert out_list == expected_list

    out_list = _slice_to_list(slice(None, 10, 1))
    assert out_list == expected_list

    out_list = _slice_to_list(slice(0, 10))
    assert out_list == expected_list

    out_list = _slice_to_list(slice(0, 10, 1))
    assert out_list == expected_list

    with pytest.raises(gapsValueError):
        _slice_to_list(slice(0, None))

    with pytest.raises(gapsValueError):
        _slice_to_list(slice(None, None))



if __name__ == "__main__":
    pytest.main(["-q", "--show-capture=all", Path(__file__), "-rapP"])
