import argparse

from ...context import mango
from ...fakes import fake_context, fake_model_state, fake_order, fake_price

from decimal import Decimal

from mango.marketmaking.orderchain.biasquoteelement import BiasQuoteElement


def test_from_args() -> None:
    args: argparse.Namespace = argparse.Namespace(biasquote_factor=[Decimal(17)])
    actual: BiasQuoteElement = BiasQuoteElement.from_command_line_parameters(args)
    assert actual.bias_factors == [17]  # type: ignore[comparison-overlap]


def test_no_factor_results_in_no_change() -> None:
    context = fake_context()
    model_state = fake_model_state(price=fake_price(price=Decimal(100)))
    actual: BiasQuoteElement = BiasQuoteElement([Decimal(1)])
    order: mango.Order = fake_order(price=Decimal(78), side=mango.Side.BUY)

    result = actual.process(context, model_state, [order])

    assert result == [order]


def test_single_factor_much_greater_than_one() -> None:
    context = fake_context()
    model_state = fake_model_state(price=fake_price(price=Decimal(100)))
    actual: BiasQuoteElement = BiasQuoteElement([Decimal("1.2")])  # Huge bias!
    buy: mango.Order = fake_order(price=Decimal(90), side=mango.Side.BUY)
    sell: mango.Order = fake_order(price=Decimal(110), side=mango.Side.SELL)

    result = actual.process(context, model_state, [buy, sell])

    assert result[0].price == 108  # 90 * 1.2 = 108
    assert result[1].price == 132  # 110 * 1.2 = 132


def test_single_factor_much_less_than_one() -> None:
    context = fake_context()
    model_state = fake_model_state(price=fake_price(price=Decimal(100)))
    actual: BiasQuoteElement = BiasQuoteElement([Decimal("0.8")])  # Huge bias!
    buy: mango.Order = fake_order(price=Decimal(90), side=mango.Side.BUY)
    sell: mango.Order = fake_order(price=Decimal(110), side=mango.Side.SELL)

    result = actual.process(context, model_state, [buy, sell])

    assert result[0].price == 72  # 90 * 0.8 = 72
    assert result[1].price == 88  # 110 * 0.8 = 88


def test_single_factor_greater_than_one() -> None:
    context = fake_context()
    model_state = fake_model_state(price=fake_price(price=Decimal(100)))
    actual: BiasQuoteElement = BiasQuoteElement([Decimal("1.001")])  # shift 10 bips up
    buy: mango.Order = fake_order(price=Decimal(90), side=mango.Side.BUY)
    sell: mango.Order = fake_order(price=Decimal(110), side=mango.Side.SELL)

    result = actual.process(context, model_state, [buy, sell])

    assert result[0].price == Decimal("90.09")  # 90 * 1.001 = 90.09
    assert result[1].price == Decimal("110.11")  # 110 * 1.001 = 110.11


def test_single_factor_less_than_one() -> None:
    context = fake_context()
    model_state = fake_model_state(price=fake_price(price=Decimal(100)))
    actual: BiasQuoteElement = BiasQuoteElement(
        [Decimal("0.999")]
    )  # shift 10 bips down
    buy: mango.Order = fake_order(price=Decimal(90), side=mango.Side.BUY)
    sell: mango.Order = fake_order(price=Decimal(110), side=mango.Side.SELL)

    result = actual.process(context, model_state, [buy, sell])

    assert result[0].price == Decimal("89.91")  # 90 * 0.999 = 89.91
    assert result[1].price == Decimal("109.89")  # 110 * 0.999 = 109.89


def test_single_factor_two_order_pairs() -> None:
    context = fake_context()
    model_state = fake_model_state(price=fake_price(price=Decimal(100)))
    actual: BiasQuoteElement = BiasQuoteElement(
        [Decimal("0.999")]
    )  # shift 10 bips down
    buy1: mango.Order = fake_order(price=Decimal(80), side=mango.Side.BUY)
    buy2: mango.Order = fake_order(price=Decimal(90), side=mango.Side.BUY)
    sell1: mango.Order = fake_order(price=Decimal(110), side=mango.Side.SELL)
    sell2: mango.Order = fake_order(price=Decimal(120), side=mango.Side.SELL)

    result = actual.process(context, model_state, [buy1, buy2, sell1, sell2])

    # Should be re-ordered as closest to top-of-book, so buy2-sell1 then buy1-sell2
    assert result[0].price == Decimal("89.91")  # 90 * 0.999 = 89.91
    assert result[1].price == Decimal("109.89")  # 110 * 0.999 = 109.89
    assert result[2].price == Decimal("79.92")  # 80 * 0.999 = 79.92
    assert result[3].price == Decimal("119.88")  # 120 * 0.999 = 119.88


def test_two_factors_two_order_pairs() -> None:
    context = fake_context()
    model_state = fake_model_state(price=fake_price(price=Decimal(100)))
    actual: BiasQuoteElement = BiasQuoteElement(
        [Decimal("0.999"), Decimal("0.9")]
    )  # shift 10 bips down
    buy1: mango.Order = fake_order(price=Decimal(80), side=mango.Side.BUY)
    buy2: mango.Order = fake_order(price=Decimal(90), side=mango.Side.BUY)
    sell1: mango.Order = fake_order(price=Decimal(110), side=mango.Side.SELL)
    sell2: mango.Order = fake_order(price=Decimal(120), side=mango.Side.SELL)

    result = actual.process(context, model_state, [buy1, buy2, sell1, sell2])

    # Should be re-ordered as closest to top-of-book, so buy2-sell1 then buy1-sell2
    assert result[0].price == Decimal("89.91")  # 90 * 0.999 = 89.91
    assert result[1].price == Decimal("109.89")  # 110 * 0.999 = 109.89
    assert result[2].price == Decimal("72")  # 80 * 0.9 = 72
    assert result[3].price == Decimal("108")  # 120 * 0.9 = 108


def test_three_factors_three_order_pairs() -> None:
    context = fake_context()
    model_state = fake_model_state(price=fake_price(price=Decimal(100)))
    actual: BiasQuoteElement = BiasQuoteElement(
        [Decimal("0.9"), Decimal("0.8"), Decimal("0.7")]
    )  # shift 10 bips down
    buy1: mango.Order = fake_order(price=Decimal(70), side=mango.Side.BUY)
    buy2: mango.Order = fake_order(price=Decimal(80), side=mango.Side.BUY)
    buy3: mango.Order = fake_order(price=Decimal(90), side=mango.Side.BUY)
    sell1: mango.Order = fake_order(price=Decimal(110), side=mango.Side.SELL)
    sell2: mango.Order = fake_order(price=Decimal(120), side=mango.Side.SELL)
    sell3: mango.Order = fake_order(price=Decimal(130), side=mango.Side.SELL)

    result = actual.process(
        context, model_state, [buy1, buy2, buy3, sell1, sell2, sell3]
    )

    # Should be re-ordered as closest to top-of-book, so buy3-sell1 then buy2-sell2, then buy1-sell3
    assert result[0].price == Decimal("81")  # 90 * 0.9 = 81
    assert result[1].price == Decimal("99")  # 110 * 0.9 = 99
    assert result[2].price == Decimal("64")  # 80 * 0.8 = 64
    assert result[3].price == Decimal("96")  # 120 * 0.8 = 96
    assert result[4].price == Decimal("49")  # 70 * 0.7 = 49
    assert result[5].price == Decimal("91")  # 130 * 0.7 = 91
