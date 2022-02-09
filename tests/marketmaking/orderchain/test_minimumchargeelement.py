import argparse

from ...context import mango
from ...fakes import fake_context, fake_model_state, fake_order, fake_price

from decimal import Decimal

from mango.marketmaking.orderchain.minimumchargeelement import MinimumChargeElement


model_state = fake_model_state(
    price=fake_price(bid=Decimal(75), price=Decimal(80), ask=Decimal(85))
)


def test_from_args() -> None:
    args: argparse.Namespace = argparse.Namespace(
        minimumcharge_ratio=[Decimal("0.2")], minimumcharge_from_bid_ask=True
    )
    actual: MinimumChargeElement = MinimumChargeElement.from_command_line_parameters(
        args
    )
    assert actual.minimumcharge_ratios == [Decimal("0.2")]
    assert actual.minimumcharge_from_bid_ask


def test_bid_price_not_updated() -> None:
    context = fake_context()
    order: mango.Order = fake_order(price=Decimal(71), side=mango.Side.BUY)

    actual: MinimumChargeElement = MinimumChargeElement([Decimal("0.1")], False)
    result = actual.process(context, model_state, [order])

    assert result[0].price == 71


def test_bid_price_not_updated_from_bid_ask() -> None:
    context = fake_context()
    order: mango.Order = fake_order(price=Decimal(66), side=mango.Side.BUY)

    actual: MinimumChargeElement = MinimumChargeElement([Decimal("0.1")], True)
    result = actual.process(context, model_state, [order])

    assert result[0].price == 66


def test_bid_price_updated() -> None:
    context = fake_context()
    order: mango.Order = fake_order(price=Decimal(73), side=mango.Side.BUY)

    actual: MinimumChargeElement = MinimumChargeElement([Decimal("0.1")], False)
    result = actual.process(context, model_state, [order])

    assert result[0].price == 72  # 80 - (80 * 0.1)


def test_bid_price_updated_from_bid_ask() -> None:
    context = fake_context()
    order: mango.Order = fake_order(price=Decimal(73), side=mango.Side.BUY)

    actual: MinimumChargeElement = MinimumChargeElement([Decimal("0.1")], True)
    result = actual.process(context, model_state, [order])

    assert result[0].price == 67.5  # 75 - (75 * 0.1)


def test_ask_price_not_updated() -> None:
    context = fake_context()
    order: mango.Order = fake_order(price=Decimal(89), side=mango.Side.SELL)

    actual: MinimumChargeElement = MinimumChargeElement([Decimal("0.1")], False)
    result = actual.process(context, model_state, [order])

    assert result[0].price == 89


def test_ask_price_not_updated_from_bid_ask() -> None:
    context = fake_context()
    order: mango.Order = fake_order(price=Decimal(95), side=mango.Side.SELL)

    actual: MinimumChargeElement = MinimumChargeElement([Decimal("0.1")], True)
    result = actual.process(context, model_state, [order])

    assert result[0].price == 95


def test_ask_price_updated() -> None:
    context = fake_context()
    order: mango.Order = fake_order(price=Decimal(87), side=mango.Side.SELL)

    actual: MinimumChargeElement = MinimumChargeElement([Decimal("0.1")], False)
    result = actual.process(context, model_state, [order])

    assert result[0].price == 88  # 80 + (80 * 0.1)


def test_ask_price_updated_from_bid_ask() -> None:
    context = fake_context()
    order: mango.Order = fake_order(price=Decimal(87), side=mango.Side.SELL)

    actual: MinimumChargeElement = MinimumChargeElement([Decimal("0.1")], True)
    result = actual.process(context, model_state, [order])

    assert result[0].price == 93.5  # 85 + (85 * 0.1)


def test_bid_price_higher_than_mid() -> None:
    context = fake_context()
    order: mango.Order = fake_order(price=Decimal(89), side=mango.Side.BUY)

    actual: MinimumChargeElement = MinimumChargeElement([Decimal("0.1")], False)
    result = actual.process(context, model_state, [order])

    assert result[0].price == 72  # 80 - (80 * 0.1)


def test_ask_price_lower_than_mid() -> None:
    context = fake_context()
    order: mango.Order = fake_order(price=Decimal(71), side=mango.Side.SELL)

    actual: MinimumChargeElement = MinimumChargeElement([Decimal("0.1")], False)
    result = actual.process(context, model_state, [order])

    assert result[0].price == 88  # 80 + (80 * 0.1)


def test_sol_bid_price_updated() -> None:
    context = fake_context()
    model_state = fake_model_state(
        price=fake_price(bid=Decimal(181.9), price=Decimal(182), ask=Decimal(182.1))
    )
    order: mango.Order = fake_order(price=Decimal("181.91"), side=mango.Side.BUY)

    actual: MinimumChargeElement = MinimumChargeElement([Decimal("0.0005")], False)
    result = actual.process(context, model_state, [order])

    assert result[0].price == Decimal("181.909")  # 182 - (182 * 0.0005)


def test_sol_ask_price_updated() -> None:
    context = fake_context()
    model_state = fake_model_state(
        price=fake_price(bid=Decimal(181.9), price=Decimal(182), ask=Decimal(182.1))
    )
    order: mango.Order = fake_order(price=Decimal("182.09"), side=mango.Side.SELL)

    actual: MinimumChargeElement = MinimumChargeElement([Decimal("0.0005")], False)
    result = actual.process(context, model_state, [order])

    assert result[0].price == Decimal("182.091")  # 182 + (182 * 0.0005)


def test_two_minimum_charges_two_order_pairs() -> None:
    context = fake_context()
    model_state = fake_model_state(price=fake_price(price=Decimal(100)))
    actual: MinimumChargeElement = MinimumChargeElement(
        [Decimal("0.1"), Decimal("0.2")], False
    )
    buy1: mango.Order = fake_order(price=Decimal(98), side=mango.Side.BUY)
    buy2: mango.Order = fake_order(price=Decimal(99), side=mango.Side.BUY)
    sell1: mango.Order = fake_order(price=Decimal(101), side=mango.Side.SELL)
    sell2: mango.Order = fake_order(price=Decimal(102), side=mango.Side.SELL)

    result = actual.process(context, model_state, [buy1, buy2, sell1, sell2])

    # Should be re-ordered as closest to top-of-book, so buy2-sell1 then buy1-sell2
    assert result[0].price == Decimal("90")  # 100 - (100 * 0.1) = 90
    assert result[1].price == Decimal("110")  # 100 + (100 * 0.1) = 110
    assert result[2].price == Decimal("80")  # 100 - (100 * 0.2) = 80
    assert result[3].price == Decimal("120")  # 100 + (100 * 0.2) = 120


def test_three_minimum_charges_three_order_pairs() -> None:
    context = fake_context()
    model_state = fake_model_state(price=fake_price(price=Decimal(100)))
    actual: MinimumChargeElement = MinimumChargeElement(
        [Decimal("0.1"), Decimal("0.2"), Decimal("0.3")], False
    )
    buy1: mango.Order = fake_order(price=Decimal(97), side=mango.Side.BUY)
    buy2: mango.Order = fake_order(price=Decimal(98), side=mango.Side.BUY)
    buy3: mango.Order = fake_order(price=Decimal(99), side=mango.Side.BUY)
    sell1: mango.Order = fake_order(price=Decimal(101), side=mango.Side.SELL)
    sell2: mango.Order = fake_order(price=Decimal(102), side=mango.Side.SELL)
    sell3: mango.Order = fake_order(price=Decimal(103), side=mango.Side.SELL)

    result = actual.process(
        context, model_state, [buy1, buy2, buy3, sell1, sell2, sell3]
    )

    # Should be re-ordered as closest to top-of-book, so buy3-sell1 then buy2-sell2 then buy1-sell3
    assert result[0].price == Decimal("90")  # 100 - (100 * 0.1) = 90
    assert result[1].price == Decimal("110")  # 100 + (100 * 0.1) = 110
    assert result[2].price == Decimal("80")  # 100 - (100 * 0.2) = 80
    assert result[3].price == Decimal("120")  # 100 + (100 * 0.2) = 120
    assert result[4].price == Decimal("70")  # 100 - (100 * 0.3) = 70
    assert result[5].price == Decimal("130")  # 100 + (100 * 0.3) = 130


def test_single_minimum_charge_three_order_pairs() -> None:
    context = fake_context()
    model_state = fake_model_state(price=fake_price(price=Decimal(100)))
    actual: MinimumChargeElement = MinimumChargeElement([Decimal("0.1")], False)
    buy1: mango.Order = fake_order(price=Decimal(97), side=mango.Side.BUY)
    buy2: mango.Order = fake_order(price=Decimal(98), side=mango.Side.BUY)
    buy3: mango.Order = fake_order(price=Decimal(99), side=mango.Side.BUY)
    sell1: mango.Order = fake_order(price=Decimal(101), side=mango.Side.SELL)
    sell2: mango.Order = fake_order(price=Decimal(102), side=mango.Side.SELL)
    sell3: mango.Order = fake_order(price=Decimal(103), side=mango.Side.SELL)

    result = actual.process(
        context, model_state, [buy1, buy2, buy3, sell1, sell2, sell3]
    )

    # Should be re-ordered as closest to top-of-book, so buy3-sell1 then buy2-sell2 then buy1-sell3
    assert result[0].price == Decimal("90")  # 100 - (100 * 0.1) = 90
    assert result[1].price == Decimal("110")  # 100 + (100 * 0.1) = 110
    assert result[2].price == Decimal("90")  # 100 - (100 * 0.1) = 90
    assert result[3].price == Decimal("110")  # 100 + (100 * 0.1) = 110
    assert result[4].price == Decimal("90")  # 100 - (100 * 0.1) = 90
    assert result[5].price == Decimal("110")  # 100 + (100 * 0.1) = 110
