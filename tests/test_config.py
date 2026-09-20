"""GAPs Config tests"""

import json
from pathlib import Path

import pytest

from gaps.config import (
    load_config,
    ConfigType,
    config_as_str_for_docstring,
    resolve_all_paths,
)
from gaps.exceptions import gapsConfigError


def test_resolve_all_paths():
    """Test resolving all paths."""

    base_dir = Path.home()

    assert resolve_all_paths("test", base_dir) == "test"
    assert resolve_all_paths("~test", base_dir) == "~test"
    assert (
        resolve_all_paths("/test/f.csv", base_dir)
        == Path("/test/f.csv").as_posix()
    )
    assert (
        resolve_all_paths("./test", base_dir) == (base_dir / "test").as_posix()
    )
    assert resolve_all_paths("../", base_dir) == base_dir.parent.as_posix()
    assert resolve_all_paths(".././", base_dir) == base_dir.parent.as_posix()
    assert (
        resolve_all_paths("../test_file.json", base_dir)
        == (base_dir.parent / "test_file.json").as_posix()
    )
    assert (
        resolve_all_paths("../test_dir/./../", base_dir)
        == base_dir.parent.as_posix()
    )
    assert (
        resolve_all_paths("test_dir/./", base_dir)
        == Path("test_dir").resolve().as_posix()
    )
    assert (
        resolve_all_paths("test_dir/../", base_dir)
        == Path("test_dir").resolve().parent.as_posix()
    )
    assert (
        resolve_all_paths("~/test_dir/../", base_dir) == Path.home().as_posix()
    )


@pytest.mark.parametrize(
    "input_,expected",
    [
        (r".\test", lambda base_dir: (base_dir / "test").as_posix()),
        (
            r"..\test_file.json",
            lambda base_dir: (base_dir.parent / "test_file.json").as_posix(),
        ),
        (
            r"test_dir\..\\test_file.json",
            lambda _base_dir: (
                Path("test_dir/../test_file.json").resolve().as_posix()
            ),
        ),
    ],
)
def test_resolve_path_windows_style_relative_paths(input_, expected):
    """Test resolving Windows-style relative paths on any host"""

    base_dir = Path.home()
    assert resolve_all_paths(input_, base_dir) == expected(base_dir)


def test_resolve_all_paths_list():
    """Test resolving all paths in a list."""
    base_dir = Path.home()
    input_ = [
        "test",
        "./test",
        "../",
        ".././",
        "../test_file.json",
        "../test_dir/./../",
        ["test", "../test_dir/./../"],
    ]
    expected_output = [
        "test",
        (base_dir / "test").as_posix(),
        base_dir.parent.as_posix(),
        base_dir.parent.as_posix(),
        (base_dir.parent / "test_file.json").as_posix(),
        base_dir.parent.as_posix(),
        ["test", base_dir.parent.as_posix()],
    ]

    assert resolve_all_paths(input_, base_dir) == expected_output


def test_resolve_all_paths_dict():
    """Test resolving all paths in a dict."""
    base_dir = Path.home()
    input_ = {
        "a": "test",
        "b": "./test",
        "c": "../",
        "d": ".././",
        "e": "../test_file.json",
        "f": "../test_dir/./../",
        "g": ["test", "../test_dir/./../"],
        "h": {
            "a": "test",
            "b": ["test", "../test_dir/./../"],
        },
    }
    expected_output = {
        "a": "test",
        "b": (base_dir / "test").as_posix(),
        "c": base_dir.parent.as_posix(),
        "d": base_dir.parent.as_posix(),
        "e": (base_dir.parent / "test_file.json").as_posix(),
        "f": base_dir.parent.as_posix(),
        "g": [
            "test",
            base_dir.parent.as_posix(),
        ],
        "h": {
            "a": "test",
            "b": [
                "test",
                base_dir.parent.as_posix(),
            ],
        },
    }

    assert resolve_all_paths(input_, base_dir) == expected_output


def test_resolve_all_paths_excluded_keys():
    """Test excluding dictionary values from path resolution."""
    base_dir = Path.home()
    command = "./my_script.py -o ./my_out_dir"
    input_ = {"cmd": command, "path": "./data.csv"}

    resolved = resolve_all_paths(input_, base_dir, excluded_keys={"cmd"})

    assert resolved["cmd"] == command
    assert resolved["path"] == (base_dir / "data.csv").as_posix()


@pytest.mark.parametrize("config_type", list(ConfigType))
def test_write_load_config(tmp_path, config_type):
    """Test loading a configuration file."""

    base_fn = f"test.{config_type}"

    test_dictionary = {"a": 1, "b": 2}
    with Path(tmp_path / base_fn).open("w", encoding="utf-8") as config_file:
        config_type.dump(test_dictionary, config_file)

    assert load_config(tmp_path / "." / base_fn) == test_dictionary

    test_dictionary = {
        "a": 1,
        "b": "A string",
        "path_a": "./config.json",
        "path_b": "./../another.json",
        "path_c": "./something/.././../another.json",
    }
    config_type.write(tmp_path / base_fn, test_dictionary)

    expected_dict = {
        "a": 1,
        "b": "A string",
        "path_a": (tmp_path / "config.json").as_posix(),
        "path_b": (tmp_path.parent / "another.json").as_posix(),
        "path_c": (tmp_path.parent / "another.json").as_posix(),
    }
    assert load_config(tmp_path / "." / base_fn) == expected_dict

    assert (
        load_config(tmp_path / "." / base_fn, resolve_paths=False)
        == test_dictionary
    )


@pytest.mark.parametrize("config_type", list(ConfigType))
def test_config_dumps_loads(config_type):
    """Test dumping and loading a configuration file to and from a str."""

    test_dictionary = {
        "a": 1,
        "b": "A string",
        "path_a": "./config.json",
        "path_b": "./../another.json",
        "path_c": "./something/.././../another.json",
    }
    assert (
        config_type.loads(config_type.dumps(test_dictionary))
        == test_dictionary
    )


@pytest.mark.parametrize("config_type", list(ConfigType))
def test_config_as_str_for_docstring(config_type):
    """Test the test_config_as_str_for_docstring function."""

    test_dictionary = {
        "a": 1,
        "b": "A string",
        "path_a": "./config.json",
        "path_b": "./../another.json",
        "path_c": "./something/.././../another.json",
    }
    as_str = config_as_str_for_docstring(test_dictionary, config_type)
    split_str = as_str.split("\n")
    assert len(split_str) >= 6
    for str_part in as_str.split("\n")[1:]:
        assert str_part.startswith("        ")


def test_load_config_json(tmp_path):
    """Test `load_config` with JSON file"""

    config_data = {"key": "value", "number": 42}
    config_file = tmp_path / "test_config.json"
    with config_file.open("w", encoding="utf-8") as f:
        json.dump(config_data, f)

    result = load_config(config_file)
    assert result == config_data


def test_load_config_json5(tmp_path):
    """Test `load_config` with JSON5 file"""

    config_content = """{
        // This is a comment
        "key": "value",
        "number": 42,
    }"""
    config_file = tmp_path / "test_config.json5"
    with config_file.open("w", encoding="utf-8") as f:
        f.write(config_content)

    result = load_config(config_file)
    assert result == {"key": "value", "number": 42}


@pytest.mark.parametrize("config_type", list(ConfigType))
def test_load_config_inherits_and_overrides(tmp_path, config_type):
    """Test recursively merging a child config over its parent."""
    parent_file = tmp_path / f"parent.{config_type}"
    child_file = tmp_path / f"child.{config_type}"
    config_type.write(
        parent_file,
        {
            "input": 1,
            "nested": {"keep": "parent", "override": "parent"},
            "items": [1, 2],
        },
    )
    config_type.write(
        child_file,
        {
            "inherit_from": parent_file.name,
            "nested": {"override": "child"},
            "items": [3],
        },
    )

    assert load_config(child_file) == {
        "input": 1,
        "nested": {"keep": "parent", "override": "child"},
        "items": [3],
    }


@pytest.mark.parametrize("config_type", list(ConfigType))
def test_load_config_deletes_inherited_keys(tmp_path, config_type):
    """Test deleting inherited keys at any mapping depth."""
    parent_file = tmp_path / f"parent.{config_type}"
    child_file = tmp_path / f"child.{config_type}"
    config_type.write(
        parent_file,
        {
            "remove": "parent",
            "nested": {"keep": 1, "remove": 2},
            "replace_scalar": "parent",
        },
    )
    config_type.write(
        child_file,
        {
            "inherit_from": parent_file.name,
            "remove": "DELETE",
            "missing": "DELETE",
            "nested": {
                "remove": "DELETE",
                "missing": "DELETE",
                "lowercase": "delete",
                "embedded": "KEEP DELETE",
            },
            "replace_scalar": {"missing": "DELETE", "keep": 3},
        },
    )

    assert load_config(child_file) == {
        "nested": {
            "keep": 1,
            "lowercase": "delete",
            "embedded": "KEEP DELETE",
        },
        "replace_scalar": {"keep": 3},
    }


def test_load_config_recursive_cross_format_inheritance(tmp_path):
    """Test inheritance, deletion, and overrides across config formats."""
    base_file = tmp_path / "base.json"
    middle_file = tmp_path / "middle.yaml"
    child_file = tmp_path / "child.toml"
    ConfigType.JSON.write(base_file, {"a": 1, "b": 2, "nested": {"c": 3}})
    ConfigType.YAML.write(
        middle_file,
        {"inherit_from": base_file.name, "b": "DELETE", "nested": {"d": 4}},
    )
    ConfigType.TOML.write(
        child_file,
        {"inherit_from": middle_file.name, "a": 10, "nested": {"c": 30}},
    )

    assert load_config(child_file) == {
        "a": 10,
        "nested": {"c": 30, "d": 4},
    }


def test_load_config_resolves_paths_from_source_config(tmp_path):
    """Test resolving inherited values relative to their source files."""
    parent_dir = tmp_path / "parents"
    child_dir = tmp_path / "children"
    parent_dir.mkdir()
    child_dir.mkdir()
    parent_file = parent_dir / "base.json"
    child_file = child_dir / "child.yaml"
    ConfigType.JSON.write(parent_file, {"parent_path": "./parent.csv"})
    ConfigType.YAML.write(
        child_file,
        {
            "inherit_from": "../parents/base.json",
            "child_path": "./child.csv",
            "cmd": "./script.py --input ./input.csv",
        },
    )

    resolved = load_config(child_file, excluded_keys={"cmd"})
    assert resolved == {
        "parent_path": (parent_dir / "parent.csv").as_posix(),
        "child_path": (child_dir / "child.csv").as_posix(),
        "cmd": "./script.py --input ./input.csv",
    }

    unresolved = load_config(child_file, resolve_paths=False)
    assert unresolved == {
        "parent_path": "./parent.csv",
        "child_path": "./child.csv",
        "cmd": "./script.py --input ./input.csv",
    }


def test_load_config_detects_inheritance_cycle(tmp_path):
    """Test reporting the complete circular inheritance chain."""
    first_file = tmp_path / "first.json"
    second_file = tmp_path / "second.yaml"
    ConfigType.JSON.write(first_file, {"inherit_from": second_file.name})
    ConfigType.YAML.write(second_file, {"inherit_from": first_file.name})

    with pytest.raises(
        gapsConfigError, match="Circular config inheritance"
    ) as exc:
        load_config(first_file)

    assert "first.json" in str(exc.value)
    assert "second.yaml" in str(exc.value)


@pytest.mark.parametrize("inherit_from", [None, "", ["parent.json"]])
def test_load_config_rejects_invalid_inheritance_value(tmp_path, inherit_from):
    """Test requiring a non-empty parent config path string."""
    config_file = tmp_path / "child.json"
    ConfigType.JSON.write(config_file, {"inherit_from": inherit_from})

    with pytest.raises(gapsConfigError, match="must be a non-empty string"):
        load_config(config_file)


def test_load_config_missing_parent(tmp_path):
    """Test exposing the resolved path when an inherited config is missing."""
    config_file = tmp_path / "child.json"
    ConfigType.JSON.write(config_file, {"inherit_from": "missing.json"})

    with pytest.raises(FileNotFoundError, match=r"missing[.]json"):
        load_config(config_file)


if __name__ == "__main__":
    pytest.main(["-q", "--show-capture=all", Path(__file__), "-rapP"])
