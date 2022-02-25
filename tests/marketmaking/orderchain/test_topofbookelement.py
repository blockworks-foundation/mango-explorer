import argparse
import typing

from ...context import mango
from ...fakes import fake_context, fake_model_state, fake_order, fake_seeded_public_key

from decimal import Decimal
from solana.publickey import PublicKey

from mango.marketmaking.orderchain.topofbookelement import TopOfBookElement

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
    args: argparse.Namespace = argparse.Namespace(topofbook_adjustment_ticks=None)
    actual: TopOfBookElement = TopOfBookElement.from_command_line_parameters(args)
    assert actual is not None


def test_bid_price_updated() -> None:
    context = fake_context()
    order: mango.Order = fake_order(
        price=Decimal(75), quantity=Decimal(7), side=mango.Side.BUY
    )

    actual: TopOfBookElement = TopOfBookElement()
    result = actual.process(context, model_state, [order])

    assert result[0].price == 79


def test_ask_price_updated() -> None:
    context = fake_context()
    order: mango.Order = fake_order(
        price=Decimal(85), quantity=Decimal(6), side=mango.Side.SELL
    )

    actual: TopOfBookElement = TopOfBookElement()
    result = actual.process(context, model_state, [order])

    assert result[0].price == 81


def test_top_check_ignores_own_orders_updated() -> None:
    order_owner: PublicKey = fake_seeded_public_key("order owner")
    bids: typing.Sequence[mango.Order] = [
        fake_order(
            price=Decimal(78), quantity=Decimal(1), side=mango.Side.BUY
        ).with_update(owner=order_owner),
        fake_order(price=Decimal(77), quantity=Decimal(2), side=mango.Side.BUY),
        fake_order(price=Decimal(76), quantity=Decimal(1), side=mango.Side.BUY),
        fake_order(
            price=Decimal(75), quantity=Decimal(5), side=mango.Side.BUY
        ).with_update(owner=order_owner),
        fake_order(price=Decimal(74), quantity=Decimal(3), side=mango.Side.BUY),
        fake_order(price=Decimal(73), quantity=Decimal(7), side=mango.Side.BUY),
    ]
    asks: typing.Sequence[mango.Order] = [
        fake_order(
            price=Decimal(82), quantity=Decimal(3), side=mango.Side.SELL
        ).with_update(owner=order_owner),
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
        price=Decimal(75), quantity=Decimal(6), side=mango.Side.BUY
    )
    sell: mango.Order = fake_order(
        price=Decimal(85), quantity=Decimal(6), side=mango.Side.SELL
    )

    actual: TopOfBookElement = TopOfBookElement()
    result = actual.process(context, model_state, [buy, sell])

    assert result[0].price == 78
    assert result[1].price == 82


def test_bid_price_updated_at_instead_of_after() -> None:
    context = fake_context()
    order: mango.Order = fake_order(
        price=Decimal(75), quantity=Decimal(7), side=mango.Side.BUY
    )

    actual: TopOfBookElement = TopOfBookElement(Decimal(0))
    result = actual.process(context, model_state, [order])

    # Should be at current best of 78, not better than current best at 79
    assert result[0].price == 78


def test_ask_price_updated_at_instead_of_after() -> None:
    context = fake_context()
    order: mango.Order = fake_order(
        price=Decimal(85), quantity=Decimal(6), side=mango.Side.SELL
    )

    actual: TopOfBookElement = TopOfBookElement(Decimal(0))
    result = actual.process(context, model_state, [order])

    # Should be at current best of 82, not better than current best at 82
    assert result[0].price == 82


def test_bid_price_updated_two_ticks_better() -> None:
    context = fake_context()
    order: mango.Order = fake_order(
        price=Decimal(75), quantity=Decimal(7), side=mango.Side.BUY
    )

    actual: TopOfBookElement = TopOfBookElement(Decimal(2))
    result = actual.process(context, model_state, [order])

    # Should be two ticks above current best of 78
    assert result[0].price == 80


def test_ask_price_updated_two_ticks_better() -> None:
    context = fake_context()
    order: mango.Order = fake_order(
        price=Decimal(85), quantity=Decimal(6), side=mango.Side.SELL
    )

    actual: TopOfBookElement = TopOfBookElement(Decimal(2))
    result = actual.process(context, model_state, [order])

    # Should be two ticks below current best of 82
    assert result[0].price == 80
