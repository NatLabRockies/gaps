"""GAPs CLI preprocessing tests"""

import json
import glob
from pathlib import Path

import pytest

from gaps.cli.command import CLICommandFromFunction
from gaps.cli.config import from_config
from gaps.status import Status, StatusField
from gaps.pipeline import Pipeline
from gaps.cli.preprocessing import preprocess_collect_config
from gaps.utilities import TAG
from gaps.exceptions import gapsConfigError
from gaps.warn import gapsWarning

SAMPLE_CONFIG = {
    "logging": {"log_level": "INFO"},
    "pipeline": [
        {"run": "./config.json"},
        {"collect-run": "./collect_config.json"},
    ],
}


def _record_project_points_split_range(project_points, out_dir, tag):
    """Record the project point subset received by a node."""

    out_fp = Path(out_dir) / f"split-range{tag}.json"
    out = {
        "split_range": project_points.split_range,
        "len_pp": len(project_points),
    }
    with out_fp.open("w", encoding="utf-8") as out_file:
        json.dump(out, out_file)

    return out_fp.as_posix()


def _noop_run_function():
    """No-op run function used to exercise config preprocessing."""


def test_preprocess_collect_config(tmp_path):
    """Test `preprocess_collect_config` function"""

    with pytest.raises(gapsConfigError) as exc_info:
        preprocess_collect_config({}, tmp_path, "run", collect_pattern="dne*")

    assert "Found no files to collect!" in str(exc_info)

    test_pattern = "pattern*.h5"
    (tmp_path / "pattern_sample_job_file.h5").touch()
    dne_pattern = "pattern_dne*.h5"
    expected_out_file = tmp_path / "pattern.h5"

    pattern = (tmp_path / "." / test_pattern).as_posix()
    config = {}

    config = preprocess_collect_config(config, tmp_path, "run", pattern)
    assert config["_out_path"] == (expected_out_file.as_posix(),)
    assert config["_pattern"] == ((tmp_path / test_pattern).as_posix(),)

    pattern = [
        (tmp_path / test_pattern).as_posix(),
        (tmp_path / dne_pattern).as_posix(),
    ]

    with pytest.warns(gapsWarning):
        config = preprocess_collect_config(config, tmp_path, "run", pattern)

    assert config["_out_path"] == (expected_out_file.as_posix(),)
    assert config["_pattern"] == ((tmp_path / test_pattern).as_posix(),)


def test_preprocess_collect_config_dict_input(tmp_path):
    """Test `preprocess_collect_config` function with dict input"""

    expected_out_file = tmp_path / "pattern.h5"
    expected_out_file.touch()
    expected_out_file = expected_out_file.as_posix()
    config = {}

    for out_fp in ["pattern.h5", "./pattern.h5", expected_out_file]:
        config = preprocess_collect_config(
            config,
            tmp_path,
            "run",
            collect_pattern={out_fp: expected_out_file},
        )
        assert config["_out_path"] == (expected_out_file,)
        assert config["_pattern"] == (expected_out_file,)


def test_preprocess_collect_config_pipeline_input(tmp_path):
    """Test `preprocess_collect_config` function with "PIPELINE" input"""
    config_fp = tmp_path / "pipe_config.json"
    with Path(config_fp).open("w", encoding="utf-8") as file_:
        json.dump(SAMPLE_CONFIG, file_)

    (tmp_path / "config.json").touch()
    (tmp_path / "collect_config.json").touch()

    Pipeline(config_fp)

    job_files = [
        tmp_path / "pattern_j0.h5",
        tmp_path / "another_pattern_j1.h5",
    ]
    for ind, job_file in enumerate(job_files):
        job_file.touch()
        Status.make_single_job_file(
            tmp_path,
            pipeline_step="run",
            job_name=f"test_{ind}",
            attrs={StatusField.OUT_FILE: job_file.as_posix()},
        )

    config = {}
    config = preprocess_collect_config(config, tmp_path, "collect-run")

    allowed_out_fn = {"pattern.h5", "another_pattern.h5"}
    assert len(config["_out_path"]) == 2
    assert len(config["_pattern"]) == 2
    for out_fp, pattern in zip(config["_out_path"], config["_pattern"]):
        assert any(name in out_fp for name in allowed_out_fn)
        assert out_fp == pattern.replace(f"{TAG}*", "")


def test_preprocess_collect_config_pipeline_input_ignores_untagged_file(
    tmp_path,
):
    """Test that PIPELINE collection patterns do not match untagged files."""
    config_fp = tmp_path / "pipe_config.json"
    with Path(config_fp).open("w", encoding="utf-8") as file_:
        json.dump(SAMPLE_CONFIG, file_)

    (tmp_path / "config.json").touch()
    (tmp_path / "collect_config.json").touch()

    Pipeline(config_fp)

    job_file = tmp_path / "output_file_j0.h5"
    job_file.touch()
    (tmp_path / "output_file.h5").touch()
    Status.make_single_job_file(
        tmp_path,
        pipeline_step="run",
        job_name="test_0",
        attrs={StatusField.OUT_FILE: job_file.as_posix()},
    )

    config = preprocess_collect_config({}, tmp_path, "collect-run")

    matched_files = sorted(
        Path(path)
        for path in glob.glob(config["_pattern"][0])  # noqa
    )
    assert matched_files == [job_file]


@pytest.mark.parametrize(
    ("execution_control", "expected_ranges"),
    [
        (None, [(0, 4)]),
        ({}, [(0, 4)]),
        ({"option": "local", "nodes": 2}, [(0, 4)]),
        ({"nodes": 2}, [(0, 2), (2, 4)]),
    ],
)
def test_split_project_points_into_ranges_from_config(
    tmp_path, test_ctx, runnable_script, execution_control, expected_ranges
):
    """Test project point range splitting through `from_config`."""

    config = {"project_points": [0, 1, 2, 3]}
    if execution_control is not None:
        config["execution_control"] = execution_control

    config_fp = tmp_path / "config.json"
    with config_fp.open("w", encoding="utf-8") as config_file:
        json.dump(config, config_file)

    command_config = CLICommandFromFunction(
        _record_project_points_split_range,
        name="run",
        split_keys={"project_points"},
    )

    from_config(config_fp, command_config)

    output_files = sorted(tmp_path.glob("split-range*.json"))
    observed_ranges = []
    observed_lengths = []
    for output_file in output_files:
        with output_file.open("r", encoding="utf-8") as file_:
            output = json.load(file_)
        observed_ranges.append(tuple(output["split_range"]))
        observed_lengths.append(output["len_pp"])

    assert observed_ranges == expected_ranges
    assert observed_lengths == [end - start for start, end in expected_ranges]


@pytest.mark.parametrize(
    ("execution_control", "expected_nodes"),
    [
        (None, 1),
        ({}, 1),
        ({"option": "local", "nodes": 2}, 1),
        (
            {
                "option": "kestrel",
                "allocation": "test-allocation",
                "walltime": 1,
                "nodes": 3,
                "num_test_nodes": 0,
            },
            3,
        ),
    ],
)
def test_preprocessor_receives_nodes_from_execution_control(
    tmp_path, test_ctx, execution_control, expected_nodes, monkeypatch
):
    """Test preprocessing functions receive normalized user node input."""

    config = {}
    if execution_control is not None:
        config["execution_control"] = execution_control

    config_fp = tmp_path / "config.json"
    with config_fp.open("w", encoding="utf-8") as config_file:
        json.dump(config, config_file)

    monkeypatch.setattr("gaps.cli.config.kickoff_job", lambda *_, **__: None)

    observed = {}

    def preprocess_config(config, nodes):
        observed["nodes"] = nodes
        return config

    command_config = CLICommandFromFunction(
        _noop_run_function,
        name="run",
        config_preprocessor=preprocess_config,
    )

    from_config(config_fp, command_config)

    assert observed["nodes"] == expected_nodes
    assert (
        command_config.documentation.template_config["execution_control"][
            "nodes"
        ]
        == 1
    )
    assert ":nodes:" in command_config.documentation.exec_control_doc


if __name__ == "__main__":
    pytest.main(["-q", "--show-capture=all", Path(__file__), "-rapP"])
