import argparse
import typing

from ...context import mango
from ...fakes import fake_context, fake_model_state, fake_order, fake_seeded_public_key

from decimal import Decimal
from solana.publickey import PublicKey

from mango.marketmaking.orderchain.afteraccumulateddepthelement import AfterAccumulatedDepthElement

bids: typing.Sequence[mango.Order] = [
    fake_order(price=Decimal(78), quantity=Decimal(1), side=mango.Side.BUY),
    fake_order(price=Decimal(77), quantity=Decimal(2), side=mango.Side.BUY),
    fake_order(price=Decimal(76), quantity=Decimal(1), side=mango.Side.BUY),
    fake_order(price=Decimal(75), quantity=Decimal(5), side=mango.Side.BUY),
    fake_order(price=Decimal(74), quantity=Decimal(3), side=mango.Side.BUY),
    fake_order(price=Decimal(73), quantity=Decimal(7), side=mango.Side.BUY)
]
asks: typing.Sequence[mango.Order] = [
    fake_order(price=Decimal(82), quantity=Decimal(3), side=mango.Side.SELL),
    fake_order(price=Decimal(83), quantity=Decimal(1), side=mango.Side.SELL),
    fake_order(price=Decimal(84), quantity=Decimal(1), side=mango.Side.SELL),
    fake_order(price=Decimal(85), quantity=Decimal(3), side=mango.Side.SELL),
    fake_order(price=Decimal(86), quantity=Decimal(3), side=mango.Side.SELL),
    fake_order(price=Decimal(87), quantity=Decimal(7), side=mango.Side.SELL)
]
model_state = fake_model_state(bids=bids, asks=asks)


def test_from_args():
    args: argparse.Namespace = argparse.Namespace()
    actual: AfterAccumulatedDepthElement = AfterAccumulatedDepthElement.from_command_line_parameters(args)
    assert actual is not None


def test_bid_price_updated():
    context = fake_context()
    order: mango.Order = fake_order(price=Decimal(78), quantity=Decimal(7), side=mango.Side.BUY)

    actual: AfterAccumulatedDepthElement = AfterAccumulatedDepthElement()
    result = actual.process(context, model_state, [order])

    assert result[0].price == 74


def test_ask_price_updated():
    context = fake_context()
    order: mango.Order = fake_order(price=Decimal(82), quantity=Decimal(6), side=mango.Side.SELL)

    actual: AfterAccumulatedDepthElement = AfterAccumulatedDepthElement()
    result = actual.process(context, model_state, [order])

    assert result[0].price == 86


def test_accumulation_ignores_own_orders_updated():
    order_owner: PublicKey = fake_seeded_public_key("order owner")
    bids: typing.Sequence[mango.Order] = [
        fake_order(price=Decimal(78), quantity=Decimal(1), side=mango.Side.BUY),
        fake_order(price=Decimal(77), quantity=Decimal(2), side=mango.Side.BUY),
        fake_order(price=Decimal(76), quantity=Decimal(1), side=mango.Side.BUY),
        fake_order(price=Decimal(75), quantity=Decimal(5), side=mango.Side.BUY).with_owner(order_owner),
        fake_order(price=Decimal(74), quantity=Decimal(3), side=mango.Side.BUY),
        fake_order(price=Decimal(73), quantity=Decimal(7), side=mango.Side.BUY)
    ]
    asks: typing.Sequence[mango.Order] = [
        fake_order(price=Decimal(82), quantity=Decimal(3), side=mango.Side.SELL),
        fake_order(price=Decimal(83), quantity=Decimal(1), side=mango.Side.SELL),
        fake_order(price=Decimal(84), quantity=Decimal(1), side=mango.Side.SELL),
        fake_order(price=Decimal(85), quantity=Decimal(3), side=mango.Side.SELL).with_owner(order_owner),
        fake_order(price=Decimal(86), quantity=Decimal(3), side=mango.Side.SELL),
        fake_order(price=Decimal(87), quantity=Decimal(7), side=mango.Side.SELL)
    ]
    model_state = fake_model_state(order_owner=order_owner, bids=bids, asks=asks)
    context = fake_context()
    buy: mango.Order = fake_order(price=Decimal(78), quantity=Decimal(6), side=mango.Side.BUY)
    sell: mango.Order = fake_order(price=Decimal(82), quantity=Decimal(6), side=mango.Side.SELL)

    actual: AfterAccumulatedDepthElement = AfterAccumulatedDepthElement()
    result = actual.process(context, model_state, [buy, sell])

    assert result[0].price == 73
    assert result[1].price == 87
