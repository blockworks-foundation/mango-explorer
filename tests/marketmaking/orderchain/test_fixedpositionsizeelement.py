import argparse

from ...context import mango
from ...fakes import fake_context, fake_model_state, fake_order, fake_price

from decimal import Decimal

from mango.marketmaking.orderchain.fixedpositionsizeelement import FixedPositionSizeElement


model_state = fake_model_state(price=fake_price(price=Decimal(80)))


def test_bid_quantity_updated():
    args: argparse.Namespace = argparse.Namespace(fixedpositionsize_value=Decimal(20))
    context = fake_context()
    order: mango.Order = fake_order(quantity=Decimal(10), side=mango.Side.BUY)

    actual: FixedPositionSizeElement = FixedPositionSizeElement(args)
    result = actual.process(context, model_state, [order])

    assert result[0].quantity == 20


def test_ask_quantity_updated():
    args: argparse.Namespace = argparse.Namespace(fixedpositionsize_value=Decimal(21))
    context = fake_context()
    order: mango.Order = fake_order(quantity=Decimal(11), side=mango.Side.SELL)

    actual: FixedPositionSizeElement = FixedPositionSizeElement(args)
    result = actual.process(context, model_state, [order])

    assert result[0].quantity == 21
