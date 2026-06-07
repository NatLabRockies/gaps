"""GAPs base utilities tests"""
from pathlib import Path

import pytest
import pandas as pd

from gaps import TEST_DATA_DIR
from gaps.utilities.io import (
    project_points_from_container_or_slice,
    _slice_to_list,
)
from gaps.exceptions import gapsValueError


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
