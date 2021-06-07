from .context import mango


def test_constructor():
    secret_key = [0] * 32
    actual = mango.Wallet(secret_key)
    assert actual is not None
    assert actual.logger is not None
    assert actual.secret_key == secret_key
    assert actual.account is not None


def test_constructor_with_longer_secret_key():
    secret_key = [0] * 64
    actual = mango.Wallet(secret_key)
    assert actual is not None
    assert actual.logger is not None
    assert actual.secret_key != secret_key
    assert len(actual.secret_key) == 32
    assert actual.account is not None
