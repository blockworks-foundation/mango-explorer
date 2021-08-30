import mango

from decimal import Decimal

from mango.marketmaking.orderchain.biasquoteonpositionelement import BiasQuoteOnPositionElement


def test_no_bias_results_in_no_change():
    actual: BiasQuoteOnPositionElement = BiasQuoteOnPositionElement(Decimal(0))
    order: mango.Order = mango.Order.from_basic_info(mango.Side.BUY, price=Decimal(1), quantity=Decimal(10))

    result = actual.bias_order(order, Decimal(100))

    assert result == order


def test_bias_with_positive_inventory():
    bias: Decimal = Decimal("0.001")
    quantity: Decimal = Decimal(10)
    inventory: Decimal = Decimal(100)
    actual: BiasQuoteOnPositionElement = BiasQuoteOnPositionElement(bias)
    order: mango.Order = mango.Order.from_basic_info(mango.Side.BUY, price=Decimal(1000), quantity=quantity)
    result = actual.bias_order(order, inventory)

    assert result != order

    # From formula:
    #   price * (1 + (curr_pos / size) * pos_lean)
    # 1000 * (1 + (100 / 10) * -0.001) == 990
    assert result.price == Decimal("990")


def test_bias_with_negative_inventory():
    bias: Decimal = Decimal("0.001")
    quantity: Decimal = Decimal(10)
    inventory: Decimal = Decimal(-100)
    actual: BiasQuoteOnPositionElement = BiasQuoteOnPositionElement(bias)
    order: mango.Order = mango.Order.from_basic_info(mango.Side.BUY, price=Decimal(1000), quantity=quantity)
    result = actual.bias_order(order, inventory)

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
def test_from_daffys_original_note():
    bias: Decimal = Decimal("0.0001")
    quantity: Decimal = Decimal("0.0002")
    inventory: Decimal = Decimal("0.0010")
    actual: BiasQuoteOnPositionElement = BiasQuoteOnPositionElement(bias)
    order: mango.Order = mango.Order.from_basic_info(mango.Side.BUY, price=Decimal(50000), quantity=quantity)
    result = actual.bias_order(order, inventory)

    assert result != order

    # 5bps of 50,000 is 25, so moved down by 25 gives:
    assert result.price == Decimal(49975)
