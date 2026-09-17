"""GAPs script command tests"""

import json
from pathlib import Path

import pytest
import pandas as pd

from gaps.cli import CLICommandFromFunction, make_cli


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
    assert "paths embedded in `cmd` are not resolved" in result.output
    assert "relative to the command's working directory" in result.output


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


if __name__ == "__main__":
    pytest.main(["-q", "--show-capture=all", Path(__file__), "-rapP"])
