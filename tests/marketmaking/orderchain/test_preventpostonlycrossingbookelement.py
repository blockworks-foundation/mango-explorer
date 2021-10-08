import argparse

from ...context import mango
from ...fakes import fake_context, fake_model_state, fake_loaded_market, fake_order

from decimal import Decimal

from mango.marketmaking.orderchain.preventpostonlycrossingbookelement import PreventPostOnlyCrossingBookElement


# The top bid is the highest price someone is willing to pay to BUY
top_bid: mango.Order = fake_order(price=Decimal(90), side=mango.Side.BUY, order_type=mango.OrderType.POST_ONLY)
# The top ask is the lowest price someone is willing to pay to SELL
top_ask: mango.Order = fake_order(price=Decimal(110), side=mango.Side.SELL, order_type=mango.OrderType.POST_ONLY)

model_state = fake_model_state(market=fake_loaded_market(), bids=[top_bid], asks=[top_ask])


def test_from_args():
    args: argparse.Namespace = argparse.Namespace()
    actual: PreventPostOnlyCrossingBookElement = PreventPostOnlyCrossingBookElement.from_command_line_parameters(args)
    assert actual is not None


def test_not_crossing_results_in_no_change():
    context = fake_context()
    order: mango.Order = fake_order(price=Decimal(100), order_type=mango.OrderType.POST_ONLY)

    actual: PreventPostOnlyCrossingBookElement = PreventPostOnlyCrossingBookElement()
    result = actual.process(context, model_state, [order])

    assert result == [order]


def test_bid_too_high_results_in_new_bid():
    context = fake_context()
    order: mango.Order = fake_order(price=Decimal(120), side=mango.Side.BUY, order_type=mango.OrderType.POST_ONLY)

    actual: PreventPostOnlyCrossingBookElement = PreventPostOnlyCrossingBookElement()
    result = actual.process(context, model_state, [order])

    assert result[0].price == 109


def test_bid_too_low_results_in_no_change():
    context = fake_context()
    order: mango.Order = fake_order(price=Decimal(80), side=mango.Side.BUY, order_type=mango.OrderType.POST_ONLY)

    actual: PreventPostOnlyCrossingBookElement = PreventPostOnlyCrossingBookElement()
    result = actual.process(context, model_state, [order])

    assert result == [order]


def test_ask_too_low_results_in_new_ask():
    context = fake_context()
    order: mango.Order = fake_order(price=Decimal(80), side=mango.Side.SELL, order_type=mango.OrderType.POST_ONLY)

    actual: PreventPostOnlyCrossingBookElement = PreventPostOnlyCrossingBookElement()
    result = actual.process(context, model_state, [order])

    assert result[0].price == 91


def test_ask_too_high_results_in_no_change():
    context = fake_context()
    order: mango.Order = fake_order(price=Decimal(120), side=mango.Side.SELL, order_type=mango.OrderType.POST_ONLY)

    actual: PreventPostOnlyCrossingBookElement = PreventPostOnlyCrossingBookElement()
    result = actual.process(context, model_state, [order])

    assert result == [order]


def test_bid_too_high_no_bid_results_in_new_bid():
    context = fake_context()
    order: mango.Order = fake_order(price=Decimal(120), side=mango.Side.BUY, order_type=mango.OrderType.POST_ONLY)

    actual: PreventPostOnlyCrossingBookElement = PreventPostOnlyCrossingBookElement()
    model_state = fake_model_state(market=fake_loaded_market(), bids=[], asks=[top_ask])

    result = actual.process(context, model_state, [order])

    assert result[0].price == 109


def test_ask_too_low_no_ask_results_in_new_ask():
    context = fake_context()
    order: mango.Order = fake_order(price=Decimal(80), side=mango.Side.SELL, order_type=mango.OrderType.POST_ONLY)

    actual: PreventPostOnlyCrossingBookElement = PreventPostOnlyCrossingBookElement()
    model_state = fake_model_state(market=fake_loaded_market(), bids=[top_bid], asks=[])
    result = actual.process(context, model_state, [order])

    assert result[0].price == 91


def test_ask_no_orderbook_results_in_no_change():
    context = fake_context()
    order: mango.Order = fake_order(price=Decimal(120), side=mango.Side.SELL, order_type=mango.OrderType.POST_ONLY)

    actual: PreventPostOnlyCrossingBookElement = PreventPostOnlyCrossingBookElement()
    model_state = fake_model_state(market=fake_loaded_market(), bids=[], asks=[])
    result = actual.process(context, model_state, [order])

    assert result == [order]


def test_bid_no_orderbook_results_in_no_change():
    context = fake_context()
    order: mango.Order = fake_order(price=Decimal(80), side=mango.Side.BUY, order_type=mango.OrderType.POST_ONLY)

    actual: PreventPostOnlyCrossingBookElement = PreventPostOnlyCrossingBookElement()
    model_state = fake_model_state(market=fake_loaded_market(), bids=[], asks=[])
    result = actual.process(context, model_state, [order])

    assert result == [order]
