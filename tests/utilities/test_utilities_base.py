"""GAPs base utilities tests"""
from pathlib import Path

import pytest

from gaps.utilities import recursively_update_dict, resolve_path
from gaps.exceptions import gapsValueError


TEST_1_ATTRS_1 = {"job_name": "test1", "job_status": "R", "run_id": 1234}
TEST_1_ATTRS_2 = {"job_name": "test1", "job_status": "successful"}


def test_recursively_update_dict():
    """Test a recursive merge of two dictionaries"""

    test = recursively_update_dict(
        {"generation": TEST_1_ATTRS_1}, {"generation": TEST_1_ATTRS_2}
    )

    assert test["generation"]["job_name"] == TEST_1_ATTRS_1["job_name"]
    assert test["generation"]["run_id"] == TEST_1_ATTRS_1["run_id"]
    assert test["generation"]["job_status"] == TEST_1_ATTRS_2["job_status"]


def test_resolve_path():
    """Test resolving path"""

    base_dir = Path.home()

    assert resolve_path("test", base_dir) == "test"
    assert resolve_path("~test", base_dir) == "~test"
    assert (
        resolve_path("/test/f.csv", base_dir) == Path("/test/f.csv").as_posix()
    )
    assert resolve_path("./test", base_dir) == (base_dir / "test").as_posix()
    assert resolve_path("../", base_dir) == base_dir.parent.as_posix()
    assert resolve_path(".././", base_dir) == base_dir.parent.as_posix()
    assert (
        resolve_path("../test_file.json", base_dir)
        == (base_dir.parent / "test_file.json").as_posix()
    )
    assert (
        resolve_path("../test_dir/./../", base_dir)
        == base_dir.parent.as_posix()
    )
    assert (
        resolve_path("test_dir/./", base_dir)
        == Path("test_dir").resolve().as_posix()
    )
    assert (
        resolve_path("test_dir/../", base_dir)
        == Path("test_dir").resolve().parent.as_posix()
    )
    assert resolve_path("~/test_dir/../", base_dir) == Path.home().as_posix()


if __name__ == "__main__":
    pytest.main(["-q", "--show-capture=all", Path(__file__), "-rapP"])
