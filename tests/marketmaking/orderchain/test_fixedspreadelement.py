import argparse

from ...context import mango
from ...fakes import fake_context, fake_model_state, fake_order, fake_price

from decimal import Decimal

from mango.marketmaking.orderchain.fixedspreadelement import FixedSpreadElement


model_state = fake_model_state(price=fake_price(price=Decimal(80)))


def test_bid_price_updated():
    args: argparse.Namespace = argparse.Namespace(fixedspread_value=Decimal(9))
    context = fake_context()
    order: mango.Order = fake_order(price=Decimal(78), side=mango.Side.BUY)

    actual: FixedSpreadElement = FixedSpreadElement(args)
    result = actual.process(context, model_state, [order])

    assert result[0].price == 71


def test_ask_price_updated():
    args: argparse.Namespace = argparse.Namespace(fixedspread_value=Decimal(9))
    context = fake_context()
    order: mango.Order = fake_order(price=Decimal(78), side=mango.Side.SELL)

    actual: FixedSpreadElement = FixedSpreadElement(args)
    result = actual.process(context, model_state, [order])

    assert result[0].price == 89
