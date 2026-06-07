"""GAPs enum tests"""
from pathlib import Path

import pytest
from gaps.utilities.enums import CaseInsensitiveEnum


def test_case_insensitive_enum():
    """Tets subclassing the case insensitive enum"""

    class TestEnum(CaseInsensitiveEnum):
        """A test enum."""

        HELLO = "hello"
        THERE = "THERE"
        THIS = "ThIS"

        @classmethod
        def _new_post_hook(cls, obj, value):
            obj.my_test_len = len(value)
            return obj

    assert f"{TestEnum.HELLO}" == "hello"
    assert f"{TestEnum.THERE}" == "there"
    assert f"{TestEnum.THIS}" == "this"

    for text in ["hello", " HELLO", " HeLlo  "]:
        assert TestEnum(text) == TestEnum.HELLO

    for text in ["there", " THERE", " ThEre  "]:
        assert TestEnum(text) == TestEnum.THERE

    for text in ["this", " THIS", " ThIs  "]:
        assert TestEnum(text) == TestEnum.THIS

    with pytest.raises(ValueError):
        TestEnum("dne")

    with pytest.raises(ValueError):
        TestEnum("DNE")

    with pytest.raises(ValueError):
        TestEnum("DnE")

    with pytest.raises(ValueError):
        TestEnum(None)

    assert TestEnum.HELLO.my_test_len == 5
    assert TestEnum.THERE.my_test_len == 5
    assert TestEnum.THIS.my_test_len == 4

    assert TestEnum.members_as_str() == {"hello", "there", "this"}


if __name__ == "__main__":
    pytest.main(["-q", "--show-capture=all", Path(__file__), "-rapP"])
