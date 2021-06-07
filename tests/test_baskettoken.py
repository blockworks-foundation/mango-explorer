from .context import mango
from .fakes import fake_index, fake_seeded_public_key, fake_token


def test_constructor():
    token = fake_token()
    vault = fake_seeded_public_key("vault")
    index = fake_index()
    actual = mango.BasketToken(token, vault, index)
    assert actual is not None
    assert actual.logger is not None
    assert actual.token == token
    assert actual.vault == vault
    assert actual.index == index
