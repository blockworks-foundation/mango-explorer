import argparse

from ...context import mango
from ...fakes import fake_context, fake_model_state, fake_order

from mango.marketmaking.orderchain.quotesinglesideelement import QuoteSingleSideElement


def test_from_args() -> None:
    args: argparse.Namespace = argparse.Namespace(quotesingleside_side=mango.Side.BUY)
    actual: QuoteSingleSideElement = (
        QuoteSingleSideElement.from_command_line_parameters(args)
    )
    assert actual is not None
    assert isinstance(actual, QuoteSingleSideElement)


def test_allow_single_buy() -> None:
    context = fake_context()
    model_state = fake_model_state()
    order: mango.Order = fake_order(side=mango.Side.BUY)

    actual: QuoteSingleSideElement = QuoteSingleSideElement(mango.Side.BUY)
    result = actual.process(context, model_state, [order])

    assert result == [order]


def test_prevent_single_buy() -> None:
    context = fake_context()
    model_state = fake_model_state()
    order: mango.Order = fake_order(side=mango.Side.BUY)

    actual: QuoteSingleSideElement = QuoteSingleSideElement(mango.Side.SELL)
    result = actual.process(context, model_state, [order])

    assert result == []


def test_allow_all_buys_and_no_sells() -> None:
    context = fake_context()
    model_state = fake_model_state()
    orders = [
        fake_order(side=mango.Side.BUY),
        fake_order(side=mango.Side.SELL),
        fake_order(side=mango.Side.BUY),
        fake_order(side=mango.Side.SELL),
        fake_order(side=mango.Side.BUY),
        fake_order(side=mango.Side.SELL),
    ]

    actual: QuoteSingleSideElement = QuoteSingleSideElement(mango.Side.BUY)
    result = actual.process(context, model_state, orders)

    assert len(result) == 3
    assert result == [orders[0], orders[2], orders[4]]


def test_allow_all_sells_and_no_buys() -> None:
    context = fake_context()
    model_state = fake_model_state()
    orders = [
        fake_order(side=mango.Side.BUY),
        fake_order(side=mango.Side.SELL),
        fake_order(side=mango.Side.BUY),
        fake_order(side=mango.Side.SELL),
        fake_order(side=mango.Side.BUY),
        fake_order(side=mango.Side.SELL),
    ]

    actual: QuoteSingleSideElement = QuoteSingleSideElement(mango.Side.SELL)
    result = actual.process(context, model_state, orders)

    assert len(result) == 3
    assert result == [orders[1], orders[3], orders[5]]


def test_allow_all_buys_and_no_sells_different_pattern() -> None:
    # This is just to check it isn't allowing every other order.
    context = fake_context()
    model_state = fake_model_state()
    orders = [
        fake_order(side=mango.Side.BUY),
        fake_order(side=mango.Side.BUY),
        fake_order(side=mango.Side.SELL),
        fake_order(side=mango.Side.SELL),
        fake_order(side=mango.Side.SELL),
        fake_order(side=mango.Side.BUY),
    ]

    actual: QuoteSingleSideElement = QuoteSingleSideElement(mango.Side.BUY)
    result = actual.process(context, model_state, orders)

    assert len(result) == 3
    assert result == [orders[0], orders[1], orders[5]]
