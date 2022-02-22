import argparse

from ...context import mango
from ...fakes import fake_context, fake_model_state, fake_price

from datetime import timedelta
from decimal import Decimal

from mango.marketmaking.orderchain.ratioselement import RatiosElement


model_state = fake_model_state(
    price=fake_price(bid=Decimal(75), price=Decimal(80), ask=Decimal(85))
)


def test_from_args() -> None:
    args: argparse.Namespace = argparse.Namespace(
        ratios_spread=[Decimal("0.7")],
        ratios_position_size=[Decimal("0.27")],
        expire_seconds=Decimal(5),
        match_limit=10,
        order_type=mango.OrderType.IOC,
        ratios_from_bid_ask=True,
    )
    actual: RatiosElement = RatiosElement.from_command_line_parameters(args)
    assert actual.order_type == mango.OrderType.IOC
    assert actual.spread_ratios == [Decimal("0.7")]
    assert actual.position_size_ratios == [Decimal("0.27")]
    assert actual.from_bid_ask
    assert actual.match_limit == 10
    assert actual.expire_seconds == Decimal(5)


def test_uses_specified_order_parameters() -> None:
    context = fake_context()

    actual: RatiosElement = RatiosElement(
        mango.OrderType.POST_ONLY_SLIDE,
        Decimal(5),
        15,
        [Decimal("0.1")],
        [Decimal("0.01")],
        False,
    )
    result = actual.process(context, model_state, [])

    assert result[0].expiration > mango.utc_now() - timedelta(seconds=1)
    assert result[0].expiration < mango.utc_now() + timedelta(seconds=5)
    assert result[0].match_limit == 15
    assert result[0].order_type == mango.OrderType.POST_ONLY_SLIDE


def test_uses_specified_spread_ratio() -> None:
    context = fake_context()

    actual: RatiosElement = RatiosElement(
        mango.OrderType.POST_ONLY,
        None,
        20,
        [Decimal("0.1")],
        [Decimal("0.01")],
        False,
    )
    result = actual.process(context, model_state, [])

    assert result[0].price == Decimal("72")
    assert result[0].quantity == Decimal("0.0125")
    assert result[1].price == Decimal("88")
    assert result[1].quantity == Decimal("0.0125")


def test_uses_specified_position_size_ratio() -> None:
    context = fake_context()

    actual: RatiosElement = RatiosElement(
        mango.OrderType.POST_ONLY,
        None,
        20,
        [Decimal("0.01")],
        [Decimal("0.1")],
        False,
    )
    result = actual.process(context, model_state, [])

    assert result[0].price == Decimal("79.2")
    assert result[0].quantity == Decimal("0.125")
    assert result[1].price == Decimal("80.8")
    assert result[1].quantity == Decimal("0.125")


def test_uses_specified_spread_and_position_size_ratio() -> None:
    context = fake_context()

    actual: RatiosElement = RatiosElement(
        mango.OrderType.POST_ONLY,
        None,
        20,
        [Decimal("0.1")],
        [Decimal("0.1")],
        False,
    )
    result = actual.process(context, model_state, [])

    assert result[0].price == Decimal("72")
    assert result[0].quantity == Decimal("0.125")
    assert result[1].price == Decimal("88")
    assert result[1].quantity == Decimal("0.125")


def test_uses_specified_spread_and_position_size_ratio_from_bid_ask() -> None:
    context = fake_context()

    actual: RatiosElement = RatiosElement(
        mango.OrderType.POST_ONLY,
        None,
        20,
        [Decimal("0.1")],
        [Decimal("0.1")],
        True,
    )
    result = actual.process(context, model_state, [])

    assert result[0].price == Decimal("67.5")
    assert result[0].quantity == Decimal("0.125")
    assert result[1].price == Decimal("93.5")
    assert result[1].quantity == Decimal("0.125")
