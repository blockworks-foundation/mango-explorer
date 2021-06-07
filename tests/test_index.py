from .context import mango

from decimal import Decimal

import datetime


def test_constructor():
    last_update = datetime.datetime.now()
    borrow = Decimal(27)
    deposit = Decimal(62)
    actual = mango.Index(mango.Version.V1, last_update, borrow, deposit)
    assert actual is not None
    assert actual.logger is not None
    assert actual.last_update == last_update
    assert actual.borrow == borrow
    assert actual.deposit == deposit
