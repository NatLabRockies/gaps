"""GAPs enums"""

from enum import Enum


class CaseInsensitiveEnum(str, Enum):
    """A string enum that is case insensitive"""

    def __new__(cls, value):
        """Create new enum member"""

        value = value.lower().strip()
        obj = str.__new__(cls, value)
        obj._value_ = value
        return cls._new_post_hook(obj, value)

    def __format__(self, format_spec):
        return str.__format__(self._value_, format_spec)

    @classmethod
    def _missing_(cls, value):
        """Convert value to lowercase before lookup"""
        if value is None:
            return None

        value = value.lower().strip()
        for member in cls:
            if member.value == value:
                return member

        return None

    @classmethod
    def _new_post_hook(cls, obj, value):  # ruff:ignore[unused-class-method-argument]
        """Hook for post-processing after __new__"""
        return obj

    @classmethod
    def members_as_str(cls):
        """Set of enum members as strings"""
        return {member.value for member in cls}
