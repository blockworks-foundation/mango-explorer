from .context import mango


def test_equality():
    assert mango.Version.V1 == mango.Version.V1


def test_inequality():
    assert mango.Version.V1 != mango.Version.V2
