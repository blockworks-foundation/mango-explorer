import argparse

from ...context import mango
from ...fakes import fake_context, fake_model_state, fake_order, fake_price

from decimal import Decimal

from mango.marketmaking.orderchain.fixedspreadelement import FixedSpreadElement


model_state = fake_model_state(price=fake_price(price=Decimal(80)))


def test_from_args() -> None:
    args: argparse.Namespace = argparse.Namespace(fixedspread_value=[Decimal(17)])
    actual: FixedSpreadElement = FixedSpreadElement.from_command_line_parameters(args)
    assert actual.spreads == [17]  # type: ignore[comparison-overlap]


def test_single_bid_price_updated() -> None:
    context = fake_context()
    order: mango.Order = fake_order(price=Decimal(78), side=mango.Side.BUY)

    actual: FixedSpreadElement = FixedSpreadElement([Decimal(9)])
    result = actual.process(context, model_state, [order])

    assert result[0].price == 75.5  # 80 - (9/2)


def test_single_ask_price_updated() -> None:
    context = fake_context()
    order: mango.Order = fake_order(price=Decimal(78), side=mango.Side.SELL)

    actual: FixedSpreadElement = FixedSpreadElement([Decimal(9)])
    result = actual.process(context, model_state, [order])

    assert result[0].price == 84.5  # 80 + (9/2)


def test_single_pair_price_updated() -> None:
    context = fake_context()
    order1: mango.Order = fake_order(price=Decimal(78), side=mango.Side.BUY)
    order2: mango.Order = fake_order(price=Decimal(78), side=mango.Side.SELL)

    actual: FixedSpreadElement = FixedSpreadElement([Decimal(9)])
    result = actual.process(context, model_state, [order1, order2])

    assert result[0].price == 75.5  # 80 - (9/2)
    assert result[1].price == 84.5  # 80 + (9/2)


def test_three_spreads_six_paired_orders_different_order_updated() -> None:
    context = fake_context()
    model_state = fake_model_state(price=fake_price(price=Decimal(10)))
    order1: mango.Order = fake_order(price=Decimal(7), side=mango.Side.BUY)
    order2: mango.Order = fake_order(price=Decimal(8), side=mango.Side.BUY)
    order3: mango.Order = fake_order(price=Decimal(9), side=mango.Side.BUY)
    order4: mango.Order = fake_order(price=Decimal(11), side=mango.Side.SELL)
    order5: mango.Order = fake_order(price=Decimal(12), side=mango.Side.SELL)
    order6: mango.Order = fake_order(price=Decimal(13), side=mango.Side.SELL)

    actual: FixedSpreadElement = FixedSpreadElement(
        [Decimal(4), Decimal(6), Decimal(8)]
    )
    result = actual.process(
        context, model_state, [order4, order3, order1, order2, order6, order5]
    )

    assert result[0].price == 8
    assert result[1].price == 12
    assert result[2].price == 7
    assert result[3].price == 13
    assert result[4].price == 6
    assert result[5].price == 14


def test_two_spreads_six_paired_orders_different_order_updated() -> None:
    context = fake_context()
    model_state = fake_model_state(price=fake_price(price=Decimal(10)))
    order1: mango.Order = fake_order(price=Decimal(7), side=mango.Side.BUY)
    order2: mango.Order = fake_order(price=Decimal(8), side=mango.Side.BUY)
    order3: mango.Order = fake_order(price=Decimal(9), side=mango.Side.BUY)
    order4: mango.Order = fake_order(price=Decimal(11), side=mango.Side.SELL)
    order5: mango.Order = fake_order(price=Decimal(12), side=mango.Side.SELL)
    order6: mango.Order = fake_order(price=Decimal(13), side=mango.Side.SELL)

    actual: FixedSpreadElement = FixedSpreadElement([Decimal(4), Decimal(6)])
    result = actual.process(
        context, model_state, [order4, order3, order1, order2, order6, order5]
    )

    assert result[0].price == 8
    assert result[1].price == 12
    assert result[2].price == 7
    assert result[3].price == 13

    # Should just use the last specified size if no other available
    assert result[4].price == 7
    assert result[5].price == 13
