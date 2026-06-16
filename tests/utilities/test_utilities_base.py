"""GAPs base utilities tests"""

from pathlib import Path

import pytest

from gaps.utilities import node_tag, recursively_update_dict, resolve_path


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


@pytest.mark.parametrize(
    ("node_index", "num_jobs", "expected"),
    [
        (0, 1, ""),
        (0, 2, "_j0"),
        (3, 10, "_j3"),
        (3, 11, "_j03"),
        (12, 101, "_j012"),
    ],
)
def test_node_tag(node_index, num_jobs, expected):
    """Test node tag generation across job counts."""

    assert node_tag(node_index, num_jobs) == expected


if __name__ == "__main__":
    pytest.main(["-q", "--show-capture=all", Path(__file__), "-rapP"])
