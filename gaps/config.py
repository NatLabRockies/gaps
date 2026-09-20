"""GAPs config functions and classes"""

import logging
import collections
from copy import deepcopy
from pathlib import Path
from abc import ABC, abstractmethod

import json
import yaml
import toml
import pyjson5

from gaps.log import init_logger
from gaps.utilities.enums import CaseInsensitiveEnum
from gaps.utilities.base import resolve_path
from gaps.exceptions import gapsConfigError, gapsValueError

logger = logging.getLogger(__name__)
_CONFIG_HANDLER_REGISTRY = {}
_INHERIT_FROM_KEY = "inherit_from"
_DELETE_SENTINEL = "DELETE"


class _JSON5Formatter:
    """Format input JSON5 data with indentation"""

    def __init__(self, data):
        self.data = data

    def _format_as_json(self):
        """Format the data input with as string with indentation"""
        return json.dumps(self.data, indent=4)


class Handler(ABC):
    """ABC for configuration file handler"""

    def __init_subclass__(cls):
        super().__init_subclass__()
        if isinstance(cls.FILE_EXTENSION, str):
            _CONFIG_HANDLER_REGISTRY[cls.FILE_EXTENSION] = cls
        else:
            for file_extension in cls.FILE_EXTENSION:
                _CONFIG_HANDLER_REGISTRY[file_extension] = cls

    @classmethod
    def load(cls, file_name):
        """Load the file contents"""
        config_str = Path(file_name).read_text(encoding="utf-8")
        return cls.loads(config_str)

    @classmethod
    def write(cls, file_name, data):
        """Write the data to a file"""
        with Path(file_name).open("w", encoding="utf-8") as config_file:
            cls.dump(data, config_file)

    @classmethod
    @abstractmethod
    def dump(cls, config, stream):
        """Write the config to a stream (file)"""

    @classmethod
    @abstractmethod
    def dumps(cls, config):
        """Convert the config to a string"""

    @classmethod
    @abstractmethod
    def loads(cls, config_str):
        """Parse the string into a config dictionary"""

    @property
    @abstractmethod
    def FILE_EXTENSION(self):  # ruff:ignore[invalid-function-name]
        """str: Enum name to use"""


class JSONHandler(Handler):
    """JSON config file handler"""

    FILE_EXTENSION = "json"
    """Expected file extension for JSON config files"""

    @classmethod
    def dump(cls, config, stream):
        """Write the config to a stream (JSON file)"""
        return json.dump(config, stream, indent=4)

    @classmethod
    def dumps(cls, config):
        """Convert the config to a JSON string"""
        return json.dumps(config, indent=4)

    @classmethod
    def loads(cls, config_str):
        """Parse the JSON string into a config dictionary"""
        return json.loads(config_str)


class JSON5Handler(Handler):
    """JSON5 config file handler"""

    FILE_EXTENSION = "json5"
    """Expected file extension for JSON5 config files"""

    @classmethod
    def dump(cls, config, stream):
        """Write the config to a stream (JSON5 file)"""
        return pyjson5.encode_io(
            _JSON5Formatter(config),
            stream,
            supply_bytes=False,
            tojson="_format_as_json",
        )

    @classmethod
    def dumps(cls, config):
        """Convert the config to a JSON5 string"""
        return pyjson5.encode(
            _JSON5Formatter(config),
            tojson="_format_as_json",
        )

    @classmethod
    def loads(cls, config_str):
        """Parse the JSON5 string into a config dictionary"""
        return pyjson5.decode(config_str, maxdepth=-1)


class YAMLHandler(Handler):
    """YAML config file handler"""

    FILE_EXTENSION = "yaml", "yml"
    """Expected file extensions for YAML config files"""

    @classmethod
    def dump(cls, config, stream):
        """Write the config to a stream (YAML file)"""
        return yaml.safe_dump(config, stream, indent=2, sort_keys=False)

    @classmethod
    def dumps(cls, config):
        """Convert the config to a YAML string"""
        return yaml.safe_dump(config, indent=2, sort_keys=False)

    @classmethod
    def loads(cls, config_str):
        """Parse the YAML string into a config dictionary"""
        return yaml.safe_load(config_str)


class TOMLHandler(Handler):
    """TOML config file handler"""

    FILE_EXTENSION = "toml"
    """Expected file extension for TOML config files"""

    @classmethod
    def dump(cls, config, stream):
        """Write the config to a stream (TOML file)"""
        return toml.dump(config, stream)

    @classmethod
    def dumps(cls, config):
        """Convert the config to a TOML string"""
        return toml.dumps(config)

    @classmethod
    def loads(cls, config_str):
        """Parse the TOML string into a config dictionary"""
        return toml.loads(config_str)


class _ConfigType(CaseInsensitiveEnum):
    """Base config type enum class only meant to be initialized once"""

    @classmethod
    def _new_post_hook(cls, obj, value):
        """Hook for post-processing after __new__; adds methods"""
        obj.dump = _CONFIG_HANDLER_REGISTRY[value].dump
        obj.dumps = _CONFIG_HANDLER_REGISTRY[value].dumps
        obj.load = _CONFIG_HANDLER_REGISTRY[value].load
        obj.loads = _CONFIG_HANDLER_REGISTRY[value].loads
        obj.write = _CONFIG_HANDLER_REGISTRY[value].write
        obj.__doc__ = f"{value} config"
        return obj


ConfigType = _ConfigType(
    "ConfigType",
    {
        config_type.upper(): config_type
        for config_type in _CONFIG_HANDLER_REGISTRY
    },
)
"""An enumeration of the available gaps config types. """


def config_as_str_for_docstring(
    config, config_type=str(ConfigType.JSON), num_spaces=12
):
    """Convert a config into a string to be used within a docstring.

    In particular, the config is serialized and extra whitespace is
    added after each newline.

    Parameters
    ----------
    config : dict
        Dictionary containing the configuration to be converted into
        docstring format.
    config_type : ConfigType, default="json"
        A :class:`ConfigType` enumeration value specifying what type
        of config file to generate. By default, "json".
    num_spaces : int, default=12
        Number of spaces to add after a newline. By default, ``12``.

    Returns
    -------
    str
        A string version of the input config, conforming to the
        specified config type.
    """
    newline_str = "".join(["\n"] + [" "] * num_spaces)
    return config_type.dumps(config).replace("\n", newline_str)


def load_config(config_filepath, resolve_paths=True, excluded_keys=None):
    """Load a config file, recursively applying inherited configuration.

    Parameters
    ----------
    config_filepath : path-like
        Path to config file.
    resolve_paths : bool, optional
        Option to (recursively) resolve file-paths in the dictionary
        w.r.t the config file directory.
        By default, ``True``.
    excluded_keys : collection of str, optional
        Dictionary keys whose values should not be resolved as paths.
        By default, ``None``.

    Returns
    -------
    dict
        Dictionary containing configuration parameters.

    Raises
    ------
    gapsConfigError
        If the inheritance value is invalid or inheritance is circular.
    gapsValueError
        If input `config_filepath` has no file ending.

    Notes
    -----
    A config may use ``inherit_from`` to name another config file.
    Parent configs are loaded recursively and dictionaries are
    deep-merged, with values from the child taking precedence. An exact
    child value of ``"DELETE"`` removes that key from the inherited
    result. Parent references and other relative paths are resolved
    relative to the file where they are defined.
    """
    return _load_config(
        config_filepath,
        resolve_paths=resolve_paths,
        excluded_keys=excluded_keys,
        inheritance_chain=(),
    )


def _load_config(
    config_filepath, resolve_paths, excluded_keys, inheritance_chain
):
    """Recursively load and merge a config inheritance chain."""

    # TODO: maybe also have a "required keys" argument
    config_filepath = Path(config_filepath).expanduser().resolve()
    if config_filepath in inheritance_chain:
        cycle = (*inheritance_chain, config_filepath)
        chain = " -> ".join(path.as_posix() for path in cycle)
        msg = f"Circular config inheritance detected: {chain}"
        raise gapsConfigError(msg)

    if "." not in config_filepath.name:
        msg = (
            f"Configuration file must have a file-ending. Got: "
            f"{config_filepath.name}"
        )
        raise gapsValueError(msg)

    config_type = ConfigType(config_filepath.name.split(".")[-1])
    config = config_type.load(config_filepath)
    has_inheritance = _INHERIT_FROM_KEY in config
    inherit_from = config.pop(_INHERIT_FROM_KEY, None)

    if resolve_paths:
        config = resolve_all_paths(
            config, config_filepath.parent, excluded_keys=excluded_keys
        )

    if not has_inheritance:
        return config

    if not isinstance(inherit_from, str) or not inherit_from.strip():
        msg = (
            f"Config inheritance key {_INHERIT_FROM_KEY!r} in "
            f"{config_filepath.as_posix()!r} must be a non-empty string"
        )
        raise gapsConfigError(msg)

    parent_filepath = Path(inherit_from).expanduser()
    if not parent_filepath.is_absolute():
        parent_filepath = config_filepath.parent / parent_filepath

    parent_config = _load_config(
        parent_filepath,
        resolve_paths=resolve_paths,
        excluded_keys=excluded_keys,
        inheritance_chain=(*inheritance_chain, config_filepath),
    )
    return _merge_configs(parent_config, config)


def _merge_configs(parent, child):
    """Deep merge a child config over a parent config."""
    merged = deepcopy(parent)
    for key, value in child.items():
        if value == _DELETE_SENTINEL:
            merged.pop(key, None)
        elif isinstance(value, collections.abc.Mapping):
            parent_value = merged.get(key, {})
            if not isinstance(parent_value, collections.abc.Mapping):
                parent_value = {}
            merged[key] = _merge_configs(parent_value, value)
        else:
            merged[key] = deepcopy(value)

    return merged


# complexipy: ignore
def resolve_all_paths(container, base_dir, excluded_keys=None):
    """Perform a deep string replacement and path resolve in `container`

    Parameters
    ----------
    container : dict | list
        Container like a dictionary or list that may (or may not)
        contain relative paths to resolve.
    base_dir : path-like
        Base path to directory from which to resolve path string
        (typically current directory)
    excluded_keys : collection of str, optional
        Dictionary keys whose values should not be resolved as paths.
        By default, ``None``.

    Returns
    -------
    container
        Input container with updated strings.
    """

    excluded_keys = set(excluded_keys or ())

    if isinstance(container, str):
        # `resolve_path` is safe to call on any string,
        # even if it is not a path
        container = resolve_path(container, Path(base_dir))

    elif isinstance(container, collections.abc.Mapping):
        container = {
            key: (
                val
                if key in excluded_keys
                else resolve_all_paths(
                    val, Path(base_dir), excluded_keys=excluded_keys
                )
            )
            for key, val in container.items()
        }

    elif isinstance(container, collections.abc.Sequence):
        container = [
            resolve_all_paths(
                item, Path(base_dir), excluded_keys=excluded_keys
            )
            for item in container
        ]

    return container


def init_logging_from_config_file(config_file, background=False):
    """Init logging, taking care of legacy rex-style kwargs.

    Parameters
    ----------
    config_file : path-like
        Path to a config file parsable as a dictionary which may or may
        not contain a "logging" key. If key not found, no further action
        is taken. If key is found, the value is expected to be a
        dictionary of keyword-argument pairs
        to :func:`gaps.log.init_logger`. rex-style keys ("log_level",
        "log_file", "log_format") are allowed. The values of these
        inputs are used to initialize a gaps logger.
    background : bool, optional
        Optional flag to specify background job initialization. If
        ``True``, then stream output is disabled. By default, ``False``.
    """
    config = load_config(config_file)
    if "logging" not in config:
        return

    kwargs = config["logging"]
    kwarg_map = {"log_level": "level", "log_file": "file", "log_format": "fmt"}
    for legacy_kwarg, new_kwarg in kwarg_map.items():
        if legacy_kwarg in kwargs:
            kwargs[new_kwarg] = kwargs.pop(legacy_kwarg)

    if background:
        kwargs["stream"] = False

    init_logger(**kwargs)
