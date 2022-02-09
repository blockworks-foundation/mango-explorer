import argparse

from ...context import mango
from ...fakes import fake_context, fake_model_state, fake_order

from decimal import Decimal

from mango.marketmaking.orderchain.roundtolotsizeelement import RoundToLotSizeElement


def test_from_args() -> None:
    args: argparse.Namespace = argparse.Namespace()
    actual: RoundToLotSizeElement = RoundToLotSizeElement.from_command_line_parameters(
        args
    )
    assert actual is not None
    assert isinstance(actual, RoundToLotSizeElement)


def test_rounds_price() -> None:
    context = fake_context()
    model_state = fake_model_state()
    order: mango.Order = fake_order(price=Decimal("1.23456789"))

    actual: RoundToLotSizeElement = RoundToLotSizeElement()
    result = actual.process(context, model_state, [order])

    assert result[0].price == 1
    assert result[0].quantity == 1


def test_rounds_quantity() -> None:
    context = fake_context()
    model_state = fake_model_state()
    order: mango.Order = fake_order(quantity=Decimal("1.23456789"))

    actual: RoundToLotSizeElement = RoundToLotSizeElement()
    result = actual.process(context, model_state, [order])

    assert result[0].price == 1
    assert result[0].quantity == Decimal("1.234568")


def test_rounds_price_and_quantity() -> None:
    context = fake_context()
    model_state = fake_model_state()
    order: mango.Order = fake_order(
        price=Decimal("1.23456789"), quantity=Decimal("1.23456789")
    )

    actual: RoundToLotSizeElement = RoundToLotSizeElement()
    result = actual.process(context, model_state, [order])

    assert result[0].price == 1
    assert result[0].quantity == Decimal("1.234568")


def test_removes_when_price_rounds_to_zero() -> None:
    context = fake_context()
    model_state = fake_model_state()
    order: mango.Order = fake_order(price=Decimal("0.0000001"))

    actual: RoundToLotSizeElement = RoundToLotSizeElement()
    result = actual.process(context, model_state, [order])

    assert len(result) == 0


def test_removes_when_quantity_rounds_to_zero() -> None:
    context = fake_context()
    model_state = fake_model_state()
    order: mango.Order = fake_order(quantity=Decimal("0.0000001"))

    actual: RoundToLotSizeElement = RoundToLotSizeElement()
    result = actual.process(context, model_state, [order])

    assert len(result) == 0


def test_removes_when_price_and_quantity_round_to_zero() -> None:
    context = fake_context()
    model_state = fake_model_state()
    order: mango.Order = fake_order(
        price=Decimal("0.0000001"), quantity=Decimal("0.0000001")
    )

    actual: RoundToLotSizeElement = RoundToLotSizeElement()
    result = actual.process(context, model_state, [order])

    assert len(result) == 0
