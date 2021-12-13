from .context import mango
from .fakes import fake_token

from decimal import Decimal


def test_constructor() -> None:
    token = fake_token()
    value = Decimal(27)
    actual = mango.InstrumentValue(token, value)
    assert actual is not None
    assert actual.token == token
    assert actual.value == value
