from .context import mango


def test_constructor() -> None:
    secret_key = bytes(bytearray([0] * 32))
    actual = mango.Wallet(secret_key)
    assert actual is not None
    assert actual.secret_key == secret_key
    assert actual.keypair is not None


def test_constructor_with_longer_secret_key() -> None:
    secret_key = bytes(bytearray([0] * 64))
    actual = mango.Wallet(secret_key)
    assert actual is not None
    assert actual.secret_key != secret_key
    assert len(actual.secret_key) == 32
    assert actual.keypair is not None
