import argparse

from ...context import mango
from ...fakes import (
    fake_context,
    fake_inventory,
    fake_model_state,
    fake_order,
    fake_price,
)

from decimal import Decimal

from mango.marketmaking.orderchain.biasquoteonpositionelement import (
    BiasQuoteOnPositionElement,
)


def test_from_args() -> None:
    args: argparse.Namespace = argparse.Namespace(
        biasquoteonposition_bias=[Decimal(17)]
    )
    actual: BiasQuoteOnPositionElement = (
        BiasQuoteOnPositionElement.from_command_line_parameters(args)
    )
    assert actual.biases == [17]  # type: ignore[comparison-overlap]


def test_no_bias_results_in_no_change() -> None:
    actual: BiasQuoteOnPositionElement = BiasQuoteOnPositionElement([])
    order: mango.Order = mango.Order.from_values(
        mango.Side.BUY, price=Decimal(1), quantity=Decimal(10)
    )

    result = actual.bias_order(order, Decimal(0), Decimal(100))

    assert result == order


def test_bias_with_positive_inventory() -> None:
    quantity: Decimal = Decimal(10)
    inventory: Decimal = Decimal(100)
    actual: BiasQuoteOnPositionElement = BiasQuoteOnPositionElement([])
    order: mango.Order = mango.Order.from_values(
        mango.Side.BUY, price=Decimal(1000), quantity=quantity
    )
    bias: Decimal = Decimal("0.001")
    result = actual.bias_order(order, bias, inventory)

    assert result != order

    # From formula:
    #   price * (1 + (curr_pos / size) * pos_lean)
    # 1000 * (1 + (100 / 10) * -0.001) == 990
    assert result.price == Decimal("990")


def test_bias_with_negative_inventory() -> None:
    quantity: Decimal = Decimal(10)
    inventory: Decimal = Decimal(-100)
    actual: BiasQuoteOnPositionElement = BiasQuoteOnPositionElement([])
    order: mango.Order = mango.Order.from_values(
        mango.Side.BUY, price=Decimal(1000), quantity=quantity
    )
    bias: Decimal = Decimal("0.001")
    result = actual.bias_order(order, bias, inventory)

    assert result != order

    # From formula:
    #   price * (1 + (curr_pos / size) * pos_lean)
    # 1000 * (1 + (-100 / 10) * -0.001) == 1010
    assert result.price == Decimal("1010")


# From Daffy on 20th August 2021:
#  Formula to adjust price might look like this `pyth_price * (1 + (curr_pos / size) * pos_lean)`
#  where pos_lean is a negative number
#
#  size is the standard size you're quoting which I believe comes from the position-size-ratio
#
#  So if my standard size I'm quoting is 0.0002 BTC, my current position is +0.0010 BTC, and pos_lean
#  is -0.0001, you would move your quotes down by 0.0005 (or 5bps)
# (Private chat link: https://discord.com/channels/@me/832570058861314048/878343278523723787)
def test_from_daffys_original_note() -> None:
    quantity: Decimal = Decimal("0.0002")
    inventory: Decimal = Decimal("0.0010")
    actual: BiasQuoteOnPositionElement = BiasQuoteOnPositionElement([])
    order: mango.Order = mango.Order.from_values(
        mango.Side.BUY, price=Decimal(50000), quantity=quantity
    )
    bias: Decimal = Decimal("0.0001")
    result = actual.bias_order(order, bias, inventory)

    assert result != order

    # 5bps of 50,000 is 25, so moved down by 25 gives:
    assert result.price == Decimal(49975)


def test_single_bias_two_order_pairs() -> None:
    context = fake_context()
    model_state = fake_model_state(
        price=fake_price(price=Decimal(100)), inventory=fake_inventory()
    )
    actual: BiasQuoteOnPositionElement = BiasQuoteOnPositionElement([Decimal("0.001")])
    buy1: mango.Order = fake_order(
        price=Decimal(80), quantity=Decimal(1), side=mango.Side.BUY
    )
    buy2: mango.Order = fake_order(
        price=Decimal(90), quantity=Decimal(2), side=mango.Side.BUY
    )
    sell1: mango.Order = fake_order(
        price=Decimal(110), quantity=Decimal(2), side=mango.Side.SELL
    )
    sell2: mango.Order = fake_order(
        price=Decimal(120), quantity=Decimal(1), side=mango.Side.SELL
    )

    result = actual.process(context, model_state, [buy1, buy2, sell1, sell2])

    # Should be re-ordered as closest to top-of-book, so buy2-sell1 then buy1-sell2
    # Formula:
    #   price * (1 + (curr_pos / size) * pos_lean)
    assert result[0].price == Decimal("89.55")  # 90 * (1 + (10 / 2) * -0.001) == 89.55
    assert result[1].price == Decimal(
        "109.45"
    )  # 110 * (1 + (10 / 2) * -0.001) == 109.45
    assert result[2].price == Decimal("79.2")  # 80 * (1 + (10 / 1) * -0.001) == 79.2
    assert result[3].price == Decimal("118.8")  # 120 * (1 + (10 / 1) * -0.001) == 118.8


def test_three_biases_three_order_pairs() -> None:
    context = fake_context()
    model_state = fake_model_state(
        price=fake_price(price=Decimal(100)), inventory=fake_inventory()
    )
    actual: BiasQuoteOnPositionElement = BiasQuoteOnPositionElement(
        [Decimal("0.001"), Decimal("0.002"), Decimal("0.003")]
    )
    buy1: mango.Order = fake_order(
        price=Decimal(70), quantity=Decimal(1), side=mango.Side.BUY
    )
    buy2: mango.Order = fake_order(
        price=Decimal(80), quantity=Decimal(2), side=mango.Side.BUY
    )
    buy3: mango.Order = fake_order(
        price=Decimal(90), quantity=Decimal(3), side=mango.Side.BUY
    )
    sell1: mango.Order = fake_order(
        price=Decimal(110), quantity=Decimal(3), side=mango.Side.SELL
    )
    sell2: mango.Order = fake_order(
        price=Decimal(120), quantity=Decimal(2), side=mango.Side.SELL
    )
    sell3: mango.Order = fake_order(
        price=Decimal(130), quantity=Decimal(1), side=mango.Side.SELL
    )

    result = actual.process(
        context, model_state, [buy1, buy2, buy3, sell1, sell2, sell3]
    )

    # Should be re-ordered as closest to top-of-book, so buy3-sell1 then buy2-sell2 then buy1-sell3
    # Formula:
    #   price * (1 + (curr_pos / size) * pos_lean)
    assert result[0].price == Decimal("89.7")  # 90 * (1 + (10 / 3) * -0.001) == 89.7
    assert (
        f"{result[1].price:.8f}" == "109.63333333"
    )  # 110 * (1 + (10 / 3) * -0.001) == 109.6333333333
    assert result[2].price == Decimal("79.2")  # 80 * (1 + (10 / 2) * -0.002) == 79.2
    assert result[3].price == Decimal("118.8")  # 120 * (1 + (10 / 2) * -0.002) == 118.8
    assert result[4].price == Decimal("67.9")  # 70 * (1 + (10 / 1) * -0.003) == 67.9
    assert result[5].price == Decimal("126.1")  # 130 * (1 + (10 / 1) * -0.003) == 126.1
