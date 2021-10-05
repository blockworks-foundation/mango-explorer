import argparse

from ...context import mango
from ...fakes import fake_context, fake_model_state, fake_price

from decimal import Decimal

from mango.marketmaking.orderchain.ratioselement import RatiosElement


model_state = fake_model_state(price=fake_price(bid=Decimal(75), price=Decimal(80), ask=Decimal(85)))


def test_no_parameters_creates_1_buy_and_sell():
    args: argparse.Namespace = argparse.Namespace(ratios_spread=None, ratios_position_size=None,
                                                  order_type=mango.OrderType.LIMIT, ratios_from_bid_ask=False)
    context = fake_context()

    actual: RatiosElement = RatiosElement(args)
    result = actual.process(context, model_state, [])

    assert result[0].price == Decimal("79.2")
    assert result[0].quantity == Decimal("0.0125")
    assert result[1].price == Decimal("80.8")
    assert result[1].quantity == Decimal("0.0125")


def test_uses_specified_spread_ratio():
    args: argparse.Namespace = argparse.Namespace(ratios_spread=[Decimal("0.1")], ratios_position_size=None,
                                                  order_type=mango.OrderType.LIMIT, ratios_from_bid_ask=False)
    context = fake_context()

    actual: RatiosElement = RatiosElement(args)
    result = actual.process(context, model_state, [])

    assert result[0].price == Decimal("72")
    assert result[0].quantity == Decimal("0.0125")
    assert result[1].price == Decimal("88")
    assert result[1].quantity == Decimal("0.0125")


def test_uses_specified_position_size_ratio():
    args: argparse.Namespace = argparse.Namespace(ratios_spread=None, ratios_position_size=[Decimal("0.1")],
                                                  order_type=mango.OrderType.LIMIT, ratios_from_bid_ask=False)
    context = fake_context()

    actual: RatiosElement = RatiosElement(args)
    result = actual.process(context, model_state, [])

    assert result[0].price == Decimal("79.2")
    assert result[0].quantity == Decimal("0.125")
    assert result[1].price == Decimal("80.8")
    assert result[1].quantity == Decimal("0.125")


def test_uses_specified_spread_and_position_size_ratio():
    args: argparse.Namespace = argparse.Namespace(ratios_spread=[Decimal("0.1")], ratios_position_size=[Decimal("0.1")],
                                                  order_type=mango.OrderType.LIMIT, ratios_from_bid_ask=False)
    context = fake_context()

    actual: RatiosElement = RatiosElement(args)
    result = actual.process(context, model_state, [])

    assert result[0].price == Decimal("72")
    assert result[0].quantity == Decimal("0.125")
    assert result[1].price == Decimal("88")
    assert result[1].quantity == Decimal("0.125")


def test_uses_specified_spread_and_position_size_ratio_from_bid_ask():
    args: argparse.Namespace = argparse.Namespace(ratios_spread=[Decimal("0.1")], ratios_position_size=[Decimal("0.1")],
                                                  order_type=mango.OrderType.LIMIT, ratios_from_bid_ask=True)
    context = fake_context()

    actual: RatiosElement = RatiosElement(args)
    result = actual.process(context, model_state, [])

    assert result[0].price == Decimal("67.5")
    assert result[0].quantity == Decimal("0.125")
    assert result[1].price == Decimal("93.5")
    assert result[1].quantity == Decimal("0.125")
