import argparse

from ...context import mango
from ...fakes import fake_context, fake_model_state, fake_order, fake_price

from decimal import Decimal

from mango.marketmaking.orderchain.biasquoteelement import BiasQuoteElement


def test_from_args():
    args: argparse.Namespace = argparse.Namespace(biasquote_factor=Decimal(17))
    actual: BiasQuoteElement = BiasQuoteElement.from_command_line_parameters(args)
    assert actual.bias_factor == 17


def test_no_factor_results_in_no_change():
    context = fake_context()
    model_state = fake_model_state(price=fake_price(price=Decimal(100)))
    actual: BiasQuoteElement = BiasQuoteElement(Decimal(1))
    order: mango.Order = fake_order(price=Decimal(78), side=mango.Side.BUY)

    result = actual.process(context, model_state, [order])

    assert result == [order]


def test_factor_much_greater_than_one():
    context = fake_context()
    model_state = fake_model_state(price=fake_price(price=Decimal(100)))
    actual: BiasQuoteElement = BiasQuoteElement(Decimal("1.2"))  # Huge bias!
    buy: mango.Order = fake_order(price=Decimal(90), side=mango.Side.BUY)
    sell: mango.Order = fake_order(price=Decimal(110), side=mango.Side.SELL)

    result = actual.process(context, model_state, [buy, sell])

    assert result[0].price == 108  # 90 * 1.2 = 108
    assert result[1].price == 132  # 110 * 1.2 = 132


def test_factor_much_less_than_one():
    context = fake_context()
    model_state = fake_model_state(price=fake_price(price=Decimal(100)))
    actual: BiasQuoteElement = BiasQuoteElement(Decimal("0.8"))  # Huge bias!
    buy: mango.Order = fake_order(price=Decimal(90), side=mango.Side.BUY)
    sell: mango.Order = fake_order(price=Decimal(110), side=mango.Side.SELL)

    result = actual.process(context, model_state, [buy, sell])

    assert result[0].price == 72  # 90 * 0.8 = 72
    assert result[1].price == 88  # 110 * 0.8 = 88


def test_factor_greater_than_one():
    context = fake_context()
    model_state = fake_model_state(price=fake_price(price=Decimal(100)))
    actual: BiasQuoteElement = BiasQuoteElement(Decimal("1.001"))  # shift 10 bips up
    buy: mango.Order = fake_order(price=Decimal(90), side=mango.Side.BUY)
    sell: mango.Order = fake_order(price=Decimal(110), side=mango.Side.SELL)

    result = actual.process(context, model_state, [buy, sell])

    assert result[0].price == Decimal("90.09")  # 90 * 1.001 = 90.09
    assert result[1].price == Decimal("110.11")  # 110 * 1.001 = 110.11


def test_factor_less_than_one():
    context = fake_context()
    model_state = fake_model_state(price=fake_price(price=Decimal(100)))
    actual: BiasQuoteElement = BiasQuoteElement(Decimal("0.999"))  # shift 10 bips down
    buy: mango.Order = fake_order(price=Decimal(90), side=mango.Side.BUY)
    sell: mango.Order = fake_order(price=Decimal(110), side=mango.Side.SELL)

    result = actual.process(context, model_state, [buy, sell])

    assert result[0].price == Decimal("89.91")  # 90 * 0.999 = 89.91
    assert result[1].price == Decimal("109.89")  # 110 * 0.999 = 109.89
