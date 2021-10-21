import argparse

from ...context import mango
from ...fakes import fake_context, fake_model_state, fake_order, fake_price

from decimal import Decimal

from mango.marketmaking.orderchain.minimumchargeelement import MinimumChargeElement


model_state = fake_model_state(price=fake_price(bid=Decimal(75), price=Decimal(80), ask=Decimal(85)))


def test_from_args():
    args: argparse.Namespace = argparse.Namespace(minimumcharge_ratio=Decimal("0.2"), minimumcharge_from_bid_ask=True)
    actual: MinimumChargeElement = MinimumChargeElement.from_command_line_parameters(args)
    assert actual.minimumcharge_ratio == Decimal("0.2")
    assert actual.minimumcharge_from_bid_ask


def test_bid_price_not_updated():
    context = fake_context()
    order: mango.Order = fake_order(price=Decimal(71), side=mango.Side.BUY)

    actual: MinimumChargeElement = MinimumChargeElement(Decimal("0.1"), False)
    result = actual.process(context, model_state, [order])

    assert result[0].price == 71


def test_bid_price_not_updated_from_bid_ask():
    context = fake_context()
    order: mango.Order = fake_order(price=Decimal(66), side=mango.Side.BUY)

    actual: MinimumChargeElement = MinimumChargeElement(Decimal("0.1"), True)
    result = actual.process(context, model_state, [order])

    assert result[0].price == 66


def test_bid_price_updated():
    context = fake_context()
    order: mango.Order = fake_order(price=Decimal(73), side=mango.Side.BUY)

    actual: MinimumChargeElement = MinimumChargeElement(Decimal("0.1"), False)
    result = actual.process(context, model_state, [order])

    assert result[0].price == 72  # 80 - (80 * 0.1)


def test_bid_price_updated_from_bid_ask():
    context = fake_context()
    order: mango.Order = fake_order(price=Decimal(73), side=mango.Side.BUY)

    actual: MinimumChargeElement = MinimumChargeElement(Decimal("0.1"), True)
    result = actual.process(context, model_state, [order])

    assert result[0].price == 67.5  # 75 - (75 * 0.1)


def test_ask_price_not_updated():
    context = fake_context()
    order: mango.Order = fake_order(price=Decimal(89), side=mango.Side.SELL)

    actual: MinimumChargeElement = MinimumChargeElement(Decimal("0.1"), False)
    result = actual.process(context, model_state, [order])

    assert result[0].price == 89


def test_ask_price_not_updated_from_bid_ask():
    context = fake_context()
    order: mango.Order = fake_order(price=Decimal(95), side=mango.Side.SELL)

    actual: MinimumChargeElement = MinimumChargeElement(Decimal("0.1"), True)
    result = actual.process(context, model_state, [order])

    assert result[0].price == 95


def test_ask_price_updated():
    context = fake_context()
    order: mango.Order = fake_order(price=Decimal(87), side=mango.Side.SELL)

    actual: MinimumChargeElement = MinimumChargeElement(Decimal("0.1"), False)
    result = actual.process(context, model_state, [order])

    assert result[0].price == 88  # 80 + (80 * 0.1)


def test_ask_price_updated_from_bid_ask():
    context = fake_context()
    order: mango.Order = fake_order(price=Decimal(87), side=mango.Side.SELL)

    actual: MinimumChargeElement = MinimumChargeElement(Decimal("0.1"), True)
    result = actual.process(context, model_state, [order])

    assert result[0].price == 93.5  # 85 + (85 * 0.1)


def test_bid_price_higher_than_mid():
    context = fake_context()
    order: mango.Order = fake_order(price=Decimal(89), side=mango.Side.BUY)

    actual: MinimumChargeElement = MinimumChargeElement(Decimal("0.1"), False)
    result = actual.process(context, model_state, [order])

    assert result[0].price == 72  # 80 - (80 * 0.1)


def test_ask_price_lower_than_mid():
    context = fake_context()
    order: mango.Order = fake_order(price=Decimal(71), side=mango.Side.SELL)

    actual: MinimumChargeElement = MinimumChargeElement(Decimal("0.1"), False)
    result = actual.process(context, model_state, [order])

    assert result[0].price == 88  # 80 + (80 * 0.1)


def test_sol_bid_price_updated():
    context = fake_context()
    model_state = fake_model_state(price=fake_price(bid=Decimal(181.9), price=Decimal(182), ask=Decimal(182.1)))
    order: mango.Order = fake_order(price=Decimal("181.91"), side=mango.Side.BUY)

    actual: MinimumChargeElement = MinimumChargeElement(Decimal("0.0005"), False)
    result = actual.process(context, model_state, [order])

    assert result[0].price == Decimal("181.909")  # 182 - (182 * 0.0005)


def test_sol_ask_price_updated():
    context = fake_context()
    model_state = fake_model_state(price=fake_price(bid=Decimal(181.9), price=Decimal(182), ask=Decimal(182.1)))
    order: mango.Order = fake_order(price=Decimal("182.09"), side=mango.Side.SELL)

    actual: MinimumChargeElement = MinimumChargeElement(Decimal("0.0005"), False)
    result = actual.process(context, model_state, [order])

    assert result[0].price == Decimal("182.091")  # 182 + (182 * 0.0005)
