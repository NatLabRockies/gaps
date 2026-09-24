"""GAPs script command tests"""

import json
import subprocess  # ruff: ignore[suspicious-subprocess-import]
from pathlib import Path

import pytest
import pandas as pd

import gaps.hpc
from gaps.cli import CLICommandFromFunction, make_cli
from gaps.status import HardwareOption


SAMPLE_SCRIPT = """
import pandas as pd
pd.DataFrame({"s": [0, 1, 34]}).to_csv("test_out.csv", index=False)
"""


def run_func():
    """Test run function"""


def test_script_cli_help(cli_runner):
    """Test that script help explains command path handling."""
    main = make_cli([CLICommandFromFunction(run_func, add_collect=False)])

    result = cli_runner.invoke(main, ["script", "--help"])

    assert result.exit_code == 0
    help_text = " ".join(result.output.split())
    assert "paths embedded in `cmd` are not resolved" in help_text
    assert "relative to the command's working directory" in help_text


def test_script_cli(tmp_path, cli_runner, runnable_script):
    """Test the script command basic execution."""

    main = make_cli([CLICommandFromFunction(run_func, add_collect=False)])

    pipe_config_fp = tmp_path / "config_pipeline.json"
    script_config_fp = tmp_path / "config_script.json"
    script_fp = tmp_path / "test.py"

    pipe_config = {
        "pipeline": [{"script": "./config_script.json"}],
        "logging": {"log_file": None, "log_level": "INFO"},
    }

    script_config = {"cmd": "python test.py -o ./my_out_dir"}

    with Path(pipe_config_fp).open("w", encoding="utf-8") as config_file:
        json.dump(pipe_config, config_file)

    with Path(script_config_fp).open("w", encoding="utf-8") as config_file:
        json.dump(script_config, config_file)

    Path(script_fp).write_text(SAMPLE_SCRIPT, encoding="utf-8")

    assert "test_out.csv" not in {f.name for f in tmp_path.glob("*")}
    assert tmp_path / "logs" not in set(tmp_path.glob("*"))
    cli_runner.invoke(main, ["pipeline", "-c", pipe_config_fp.as_posix()])
    assert len(set((tmp_path / "logs").glob("*script*"))) == 1
    assert tmp_path / "logs" in set(tmp_path.glob("*"))
    assert "test_out.csv" in {f.name for f in tmp_path.glob("*")}

    test_df = pd.read_csv(tmp_path / "test_out.csv")
    pd.testing.assert_frame_equal(test_df, pd.DataFrame({"s": [0, 1, 34]}))


def test_script_cli_can_access_execution_parameters_from_env(
    tmp_path, cli_runner, monkeypatch
):
    """Test script commands can read execution parameters from the env."""
    main = make_cli(
        [CLICommandFromFunction(run_func, add_collect=False)],
        info={"name": "test"},
    )
    config_fp = tmp_path / "config_script.json"
    script_fp = tmp_path / "read_env.py"
    output_fp = tmp_path / "execution_parameters.json"
    execution_control = {
        "option": "slurm",
        "allocation": "test-allocation",
        "walltime": 1,
        "nodes": 2,
        "num_test_nodes": 1,
        "max_workers": 3,
    }
    config = {
        "cmd": f"python {script_fp.name}",
        "execution_control": execution_control,
    }
    config_fp.write_text(json.dumps(config), encoding="utf-8")
    script_fp.write_text(
        """import json
import os

names = [
    "TEST_OPTION",
    "TEST_ALLOCATION",
    "TEST_WALLTIME",
    "TEST_NODES",
    "TEST_NUM_TEST_NODES",
    "TEST_MAX_WORKERS",
]
with open("execution_parameters.json", "w", encoding="utf-8") as file:
    json.dump({name: os.environ[name] for name in names}, file)
""",
        encoding="utf-8",
    )

    manager = HardwareOption.SLURM.manager
    monkeypatch.setattr(manager, "_queue", {})

    def _run_submission(command):
        submission_script = Path(command.split(maxsplit=1)[1])
        # ruff: ignore[subprocess-without-shell-equals-true]
        result = subprocess.run(
            # ruff: ignore[start-process-with-partial-path]
            ["bash", submission_script],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        return "Submitted batch job 9999", None

    monkeypatch.setattr(gaps.hpc, "submit", _run_submission, raising=True)

    result = cli_runner.invoke(main, ["script", "-c", str(config_fp)])

    assert result.exit_code == 0, result.exception
    assert json.loads(output_fp.read_text(encoding="utf-8")) == {
        "TEST_OPTION": "slurm",
        "TEST_ALLOCATION": "test-allocation",
        "TEST_WALLTIME": "1",
        "TEST_NODES": "2",
        "TEST_NUM_TEST_NODES": "1",
        "TEST_MAX_WORKERS": "3",
    }


if __name__ == "__main__":
    pytest.main(["-q", "--show-capture=all", Path(__file__), "-rapP"])
