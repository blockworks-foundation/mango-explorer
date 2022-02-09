import argparse

from ...context import mango
from ...fakes import fake_context, fake_model_state, fake_order, fake_price

from decimal import Decimal

from mango.marketmaking.orderchain.fixedpositionsizeelement import (
    FixedPositionSizeElement,
)


model_state = fake_model_state(price=fake_price(price=Decimal(80)))


def test_from_args() -> None:
    args: argparse.Namespace = argparse.Namespace(fixedpositionsize_value=[Decimal(17)])
    actual: FixedPositionSizeElement = (
        FixedPositionSizeElement.from_command_line_parameters(args)
    )
    assert actual.position_sizes == [17]  # type: ignore[comparison-overlap]


def test_single_bid_quantity_updated() -> None:
    context = fake_context()
    order: mango.Order = fake_order(quantity=Decimal(10), side=mango.Side.BUY)

    actual: FixedPositionSizeElement = FixedPositionSizeElement([Decimal(20)])
    result = actual.process(context, model_state, [order])

    assert result[0].quantity == 20


def test_single_ask_quantity_updated() -> None:
    context = fake_context()
    order: mango.Order = fake_order(quantity=Decimal(11), side=mango.Side.SELL)

    actual: FixedPositionSizeElement = FixedPositionSizeElement([Decimal(21)])
    result = actual.process(context, model_state, [order])

    assert result[0].quantity == 21


def test_single_quantity_multiple_orders_updated() -> None:
    context = fake_context()
    order1: mango.Order = fake_order(quantity=Decimal(9), side=mango.Side.BUY)
    order2: mango.Order = fake_order(quantity=Decimal(10), side=mango.Side.BUY)
    order3: mango.Order = fake_order(quantity=Decimal(11), side=mango.Side.SELL)
    order4: mango.Order = fake_order(quantity=Decimal(12), side=mango.Side.SELL)

    actual: FixedPositionSizeElement = FixedPositionSizeElement([Decimal(20)])
    result = actual.process(context, model_state, [order1, order2, order3, order4])

    assert result[0].quantity == 20
    assert result[1].quantity == 20
    assert result[2].quantity == 20
    assert result[3].quantity == 20


def test_three_quantities_six_paired_orders_different_order_updated() -> None:
    context = fake_context()
    order1: mango.Order = fake_order(quantity=Decimal(8), side=mango.Side.BUY)
    order2: mango.Order = fake_order(quantity=Decimal(9), side=mango.Side.BUY)
    order3: mango.Order = fake_order(quantity=Decimal(10), side=mango.Side.BUY)
    order4: mango.Order = fake_order(quantity=Decimal(11), side=mango.Side.SELL)
    order5: mango.Order = fake_order(quantity=Decimal(12), side=mango.Side.SELL)
    order6: mango.Order = fake_order(quantity=Decimal(13), side=mango.Side.SELL)

    actual: FixedPositionSizeElement = FixedPositionSizeElement(
        [Decimal(22), Decimal(33), Decimal(44)]
    )

    # This line is different from previous test - orders are in different order but should be
    # returned in the proper order
    result = actual.process(
        context, model_state, [order4, order3, order1, order2, order6, order5]
    )

    assert result[0].quantity == 22
    assert result[1].quantity == 22
    assert result[2].quantity == 33
    assert result[3].quantity == 33
    assert result[4].quantity == 44
    assert result[5].quantity == 44


def test_two_quantities_six_paired_orders_different_order_updated() -> None:
    context = fake_context()
    order1: mango.Order = fake_order(quantity=Decimal(8), side=mango.Side.BUY)
    order2: mango.Order = fake_order(quantity=Decimal(9), side=mango.Side.BUY)
    order3: mango.Order = fake_order(quantity=Decimal(10), side=mango.Side.BUY)
    order4: mango.Order = fake_order(quantity=Decimal(11), side=mango.Side.SELL)
    order5: mango.Order = fake_order(quantity=Decimal(12), side=mango.Side.SELL)
    order6: mango.Order = fake_order(quantity=Decimal(13), side=mango.Side.SELL)

    actual: FixedPositionSizeElement = FixedPositionSizeElement(
        [Decimal(22), Decimal(33)]
    )
    result = actual.process(
        context, model_state, [order4, order3, order1, order2, order6, order5]
    )

    assert result[0].quantity == 22
    assert result[1].quantity == 22
    assert result[2].quantity == 33
    assert result[3].quantity == 33

    # Should just use the last specified size if no other available
    assert result[4].quantity == 33
    assert result[5].quantity == 33
