from .context import mango


def test_equality() -> None:
    assert mango.Version.V1.value == mango.Version.V1.value


def test_inequality() -> None:
    assert mango.Version.V1.value != mango.Version.V2.value
