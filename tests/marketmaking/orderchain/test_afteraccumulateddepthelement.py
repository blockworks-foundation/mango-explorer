import argparse
import typing

from ...context import mango
from ...fakes import fake_context, fake_model_state, fake_order, fake_seeded_public_key

from decimal import Decimal
from solana.publickey import PublicKey

from mango.marketmaking.orderchain.afteraccumulateddepthelement import (
    AfterAccumulatedDepthElement,
)

bids: typing.Sequence[mango.Order] = [
    fake_order(price=Decimal(78), quantity=Decimal(1), side=mango.Side.BUY),
    fake_order(price=Decimal(77), quantity=Decimal(2), side=mango.Side.BUY),
    fake_order(price=Decimal(76), quantity=Decimal(1), side=mango.Side.BUY),
    fake_order(price=Decimal(75), quantity=Decimal(5), side=mango.Side.BUY),
    fake_order(price=Decimal(74), quantity=Decimal(3), side=mango.Side.BUY),
    fake_order(price=Decimal(73), quantity=Decimal(7), side=mango.Side.BUY),
]
asks: typing.Sequence[mango.Order] = [
    fake_order(price=Decimal(82), quantity=Decimal(3), side=mango.Side.SELL),
    fake_order(price=Decimal(83), quantity=Decimal(1), side=mango.Side.SELL),
    fake_order(price=Decimal(84), quantity=Decimal(1), side=mango.Side.SELL),
    fake_order(price=Decimal(85), quantity=Decimal(3), side=mango.Side.SELL),
    fake_order(price=Decimal(86), quantity=Decimal(3), side=mango.Side.SELL),
    fake_order(price=Decimal(87), quantity=Decimal(7), side=mango.Side.SELL),
]
orderbook: mango.OrderBook = mango.OrderBook(
    "TEST", mango.NullLotSizeConverter(), bids, asks
)
model_state = fake_model_state(orderbook=orderbook)


def test_from_args() -> None:
    args: argparse.Namespace = argparse.Namespace(
        afteraccumulateddepth_depth=None, afteraccumulateddepth_adjustment_ticks=None
    )
    actual: AfterAccumulatedDepthElement = (
        AfterAccumulatedDepthElement.from_command_line_parameters(args)
    )
    assert actual is not None


def test_bid_price_updated() -> None:
    context = fake_context()
    order: mango.Order = fake_order(
        price=Decimal(78), quantity=Decimal(7), side=mango.Side.BUY
    )

    actual: AfterAccumulatedDepthElement = AfterAccumulatedDepthElement(None)
    result = actual.process(context, model_state, [order])

    assert result[0].price == 74


def test_ask_price_updated() -> None:
    context = fake_context()
    order: mango.Order = fake_order(
        price=Decimal(82), quantity=Decimal(6), side=mango.Side.SELL
    )

    actual: AfterAccumulatedDepthElement = AfterAccumulatedDepthElement(None)
    result = actual.process(context, model_state, [order])

    assert result[0].price == 86


def test_accumulation_ignores_own_orders_updated() -> None:
    order_owner: PublicKey = fake_seeded_public_key("order owner")
    bids: typing.Sequence[mango.Order] = [
        fake_order(price=Decimal(78), quantity=Decimal(1), side=mango.Side.BUY),
        fake_order(price=Decimal(77), quantity=Decimal(2), side=mango.Side.BUY),
        fake_order(price=Decimal(76), quantity=Decimal(1), side=mango.Side.BUY),
        fake_order(
            price=Decimal(75), quantity=Decimal(5), side=mango.Side.BUY
        ).with_update(owner=order_owner),
        fake_order(price=Decimal(74), quantity=Decimal(3), side=mango.Side.BUY),
        fake_order(price=Decimal(73), quantity=Decimal(7), side=mango.Side.BUY),
    ]
    asks: typing.Sequence[mango.Order] = [
        fake_order(price=Decimal(82), quantity=Decimal(3), side=mango.Side.SELL),
        fake_order(price=Decimal(83), quantity=Decimal(1), side=mango.Side.SELL),
        fake_order(price=Decimal(84), quantity=Decimal(1), side=mango.Side.SELL),
        fake_order(
            price=Decimal(85), quantity=Decimal(3), side=mango.Side.SELL
        ).with_update(owner=order_owner),
        fake_order(price=Decimal(86), quantity=Decimal(3), side=mango.Side.SELL),
        fake_order(price=Decimal(87), quantity=Decimal(7), side=mango.Side.SELL),
    ]
    orderbook: mango.OrderBook = mango.OrderBook(
        "TEST", mango.NullLotSizeConverter(), bids, asks
    )
    model_state = fake_model_state(order_owner=order_owner, orderbook=orderbook)
    context = fake_context()
    buy: mango.Order = fake_order(
        price=Decimal(78), quantity=Decimal(6), side=mango.Side.BUY
    )
    sell: mango.Order = fake_order(
        price=Decimal(82), quantity=Decimal(6), side=mango.Side.SELL
    )

    actual: AfterAccumulatedDepthElement = AfterAccumulatedDepthElement(None)
    result = actual.process(context, model_state, [buy, sell])

    assert result[0].price == 73
    assert result[1].price == 87


def test_bid_price_updated_at_instead_of_after() -> None:
    context = fake_context()
    order: mango.Order = fake_order(
        price=Decimal(78), quantity=Decimal(7), side=mango.Side.BUY
    )

    actual: AfterAccumulatedDepthElement = AfterAccumulatedDepthElement(
        None, Decimal(0)
    )
    result = actual.process(context, model_state, [order])

    # At depth of 7, price should be 75, not 74 if it was placed after depth of 7
    assert result[0].price == 75


def test_ask_price_updated_at_instead_of_after() -> None:
    context = fake_context()
    order: mango.Order = fake_order(
        price=Decimal(82), quantity=Decimal(6), side=mango.Side.SELL
    )

    actual: AfterAccumulatedDepthElement = AfterAccumulatedDepthElement(
        None, Decimal(0)
    )
    result = actual.process(context, model_state, [order])

    # At depth of 6, price should be 85, not 74 if it was placed after depth of 6
    assert result[0].price == 85


def test_bid_price_updated_for_fixed_depth() -> None:
    context = fake_context()
    order: mango.Order = fake_order(
        price=Decimal(78), quantity=Decimal(7), side=mango.Side.BUY
    )

    actual: AfterAccumulatedDepthElement = AfterAccumulatedDepthElement(Decimal(3))
    result = actual.process(context, model_state, [order])

    # After fixed depth of 3, price should be 76 (not 74 if depth was order quantity)
    assert result[0].price == 76


def test_ask_price_updated_for_fixed_depth() -> None:
    context = fake_context()
    order: mango.Order = fake_order(
        price=Decimal(82), quantity=Decimal(6), side=mango.Side.SELL
    )

    actual: AfterAccumulatedDepthElement = AfterAccumulatedDepthElement(Decimal(3))
    result = actual.process(context, model_state, [order])

    # After fixed depth of 3, price should be 83 (not 86 if depth was order quantity)
    assert result[0].price == 83


def test_bid_price_updated_at_instead_of_after_fixed_depth() -> None:
    context = fake_context()
    order: mango.Order = fake_order(
        price=Decimal(78), quantity=Decimal(7), side=mango.Side.BUY
    )

    actual: AfterAccumulatedDepthElement = AfterAccumulatedDepthElement(
        Decimal(3), Decimal(0)
    )
    result = actual.process(context, model_state, [order])

    # At fixed depth of 3, price should be 77 (not 74 if depth was order quantity, or
    # 76 if it was after instead of at)
    assert result[0].price == 77


def test_ask_price_updated_at_instead_of_after_fixed_depth() -> None:
    context = fake_context()
    order: mango.Order = fake_order(
        price=Decimal(82), quantity=Decimal(6), side=mango.Side.SELL
    )

    actual: AfterAccumulatedDepthElement = AfterAccumulatedDepthElement(
        Decimal(3), Decimal(0)
    )
    result = actual.process(context, model_state, [order])

    # At fixed depth of 3, price should be 82 (not 86 if depth was order quantity, or
    # 83 if it was after instead of at)
    assert result[0].price == 82
