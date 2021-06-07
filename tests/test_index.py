from .context import mango
from .fakes import fake_token

from decimal import Decimal

import datetime


def test_constructor():
    last_update = datetime.datetime.now()
    token = fake_token()
    borrow = mango.TokenValue(token, Decimal(27))
    deposit = mango.TokenValue(token, Decimal(62))
    actual = mango.Index(mango.Version.V1, token, last_update, borrow, deposit)
    assert actual is not None
    assert actual.logger is not None
    assert actual.last_update == last_update
    assert actual.borrow == borrow
    assert actual.deposit == deposit
