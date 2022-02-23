from .context import mango

from datetime import timedelta
from decimal import Decimal


def test_order_expired() -> None:
    actual = mango.Order.from_basic_info(
        side=mango.Side.BUY,
        price=Decimal(10),
        quantity=Decimal(20),
        order_type=mango.OrderType.LIMIT,
        expiration=mango.utc_now() - timedelta(seconds=1),
    )

    assert actual.expired


def test_order_not_expired() -> None:
    actual = mango.Order.from_basic_info(
        side=mango.Side.BUY,
        price=Decimal(10),
        quantity=Decimal(20),
        order_type=mango.OrderType.LIMIT,
        expiration=mango.utc_now() + timedelta(seconds=5),
    )

    assert not actual.expired
