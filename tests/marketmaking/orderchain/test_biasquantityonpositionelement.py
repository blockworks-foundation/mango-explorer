import argparse
import typing

from ...context import mango
from ...fakes import (
    fake_context,
    fake_model_state,
    fake_order,
    fake_price,
    fake_inventory,
)

from dataclasses import dataclass
from decimal import Decimal

from mango.marketmaking.orderchain.biasquantityonpositionelement import (
    BiasQuantityOnPositionElement,
)


@dataclass()
class BQOPInput:
    buy: mango.Order
    sell: mango.Order
    current: Decimal
    target: Decimal
    maximum: Decimal


def __biasquantityonposition_pair(
    input_data: BQOPInput,
) -> typing.Tuple[Decimal, Decimal]:
    element: BiasQuantityOnPositionElement = BiasQuantityOnPositionElement(
        input_data.maximum, input_data.target
    )
    context = fake_context()
    model_state = fake_model_state(
        price=fake_price(price=Decimal(100)),
        inventory=fake_inventory(base=input_data.current),
    )
    buy, sell = element.process_order_pair(
        context, model_state, 0, input_data.buy, input_data.sell
    )
    if buy is None:
        raise Exception("BUY should never be None in this test")
    if sell is None:
        raise Exception("SELL should never be None in this test")
    return buy.quantity, sell.quantity


def test_from_args() -> None:
    args: argparse.Namespace = argparse.Namespace(
        biasquantityonposition_maximum_position=Decimal(17),
        biasquantityonposition_target_position=Decimal(7),
    )
    actual: BiasQuantityOnPositionElement = (
        BiasQuantityOnPositionElement.from_command_line_parameters(args)
    )
    assert actual.maximum_position == 17
    assert actual.target_position == 7


def test_constructor() -> None:
    actual: BiasQuantityOnPositionElement = BiasQuantityOnPositionElement(
        Decimal(17), Decimal(7)
    )
    assert actual.maximum_position == 17
    assert actual.target_position == 7


def test_constructor_no_target() -> None:
    actual: BiasQuantityOnPositionElement = BiasQuantityOnPositionElement(Decimal(17))
    assert actual.maximum_position == 17
    assert actual.target_position == 0


def test_table_target_zero() -> None:
    # This table is taken from the docs/BiasQuantityOnPosition.ods spreadsheet.
    #
    # BUY	SELL	POSITION	MAX POSITION	TARGET	ADJUSTED BUY	ADJUSTED SELL
    # 10	10	    0	        50	            0	        10          	10
    # 10	10	    10	        50	            0	        8           	12
    # 10	10	    20	        50	            0	        6           	14
    # 10	10	    30	        50	            0	        4           	16
    # 10	10	    40	        50	            0	        2           	18
    # 10	10	    50	        50	            0	        0           	20
    # 10	10	    60	        50	            0	        0           	20
    # 10	10	    -10	        50	            0	        12          	8
    # 10	10	    -20	        50	            0	        14          	6
    # 10	10	    -30	        50	            0	        16          	4
    # 10	10	    -40	        50	            0	        18          	2
    # 10	10	    -50	        50	            0	        20          	0
    # 10	10	    -60	        50	            0	        20          	0
    buy: mango.Order = fake_order(quantity=Decimal(10), side=mango.Side.BUY)
    sell: mango.Order = fake_order(quantity=Decimal(10), side=mango.Side.SELL)
    target: Decimal = Decimal(0)
    positions: typing.Sequence[int] = [
        0,
        10,
        20,
        30,
        40,
        50,
        60,
        -10,
        -20,
        -30,
        -40,
        -50,
        -60,
    ]
    adjusted_buys: typing.Sequence[int] = [10, 8, 6, 4, 2, 0, 0, 12, 14, 16, 18, 20, 20]
    adjusted_sells: typing.Sequence[int] = [
        10,
        12,
        14,
        16,
        18,
        20,
        20,
        8,
        6,
        4,
        2,
        0,
        0,
    ]
    for index, position in enumerate(positions):
        buy_quantity, sell_quantity = __biasquantityonposition_pair(
            BQOPInput(buy, sell, Decimal(position), target, Decimal(50))
        )
        assert buy_quantity == Decimal(adjusted_buys[index])
        assert sell_quantity == Decimal(adjusted_sells[index])


def test_table_fractional_target_zero() -> None:
    # This table is taken from the docs/BiasQuantityOnPosition.ods spreadsheet.
    #
    # BUY	SELL	POSITION	MAX POSITION	TARGET	ADJUSTED BUY	ADJUSTED SELL
    # 0.25	0.25    	2       	4           	0   	0.125       	0.375
    # 0.25	0.25    	-2      	4           	0   	0.375       	0.125
    buy: mango.Order = fake_order(quantity=Decimal("0.25"), side=mango.Side.BUY)
    sell: mango.Order = fake_order(quantity=Decimal("0.25"), side=mango.Side.SELL)
    target: Decimal = Decimal(0)
    positions: typing.Sequence[int] = [2, -2]
    adjusted_buys: typing.Sequence[Decimal] = [Decimal("0.125"), Decimal("0.375")]
    adjusted_sells: typing.Sequence[Decimal] = [Decimal("0.375"), Decimal("0.125")]
    for index, position in enumerate(positions):
        buy_quantity, sell_quantity = __biasquantityonposition_pair(
            BQOPInput(buy, sell, Decimal(position), target, Decimal(4))
        )
        assert buy_quantity == adjusted_buys[index]
        assert sell_quantity == adjusted_sells[index]


def test_table_negative_target() -> None:
    # This table is taken from the docs/BiasQuantityOnPosition.ods spreadsheet.
    #
    # BUY	SELL	POSITION	MAX POSITION	TARGET	ADJUSTED BUY	ADJUSTED SELL
    # 10	10      	0       	50      	-10     	8           	12
    # 10	10      	10      	50      	-10     	6           	14
    # 10	10      	20      	50      	-10     	4           	16
    # 10	10      	30      	50      	-10     	2           	18
    # 10	10      	40      	50      	-10     	0           	20
    # 10	10      	50      	50      	-10     	0           	20
    # 10	10      	60      	50      	-10     	0           	20
    # 10	10      	-10     	50      	-10     	10          	10
    # 10	10      	-20     	50      	-10     	12          	8
    # 10	10      	-30     	50      	-10     	14          	6
    # 10	10      	-40     	50      	-10     	16          	4
    # 10	10      	-50     	50      	-10     	18          	2
    # 10	10      	-60     	50      	-10     	20          	0
    buy: mango.Order = fake_order(quantity=Decimal(10), side=mango.Side.BUY)
    sell: mango.Order = fake_order(quantity=Decimal(10), side=mango.Side.SELL)
    target: Decimal = Decimal(-10)
    positions: typing.Sequence[int] = [
        0,
        10,
        20,
        30,
        40,
        50,
        60,
        -10,
        -20,
        -30,
        -40,
        -50,
        -60,
    ]
    adjusted_buys: typing.Sequence[int] = [8, 6, 4, 2, 0, 0, 0, 10, 12, 14, 16, 18, 20]
    adjusted_sells: typing.Sequence[int] = [
        12,
        14,
        16,
        18,
        20,
        20,
        20,
        10,
        8,
        6,
        4,
        2,
        0,
    ]
    for index, position in enumerate(positions):
        buy_quantity, sell_quantity = __biasquantityonposition_pair(
            BQOPInput(buy, sell, Decimal(position), target, Decimal(50))
        )
        assert buy_quantity == Decimal(adjusted_buys[index])
        assert sell_quantity == Decimal(adjusted_sells[index])


def test_table_fractional_negative_target() -> None:
    # This table is taken from the docs/BiasQuantityOnPosition.ods spreadsheet.
    #
    # BUY	SELL	POSITION	MAX POSITION	TARGET	ADJUSTED BUY	ADJUSTED SELL
    # 0.25	0.25    	0       	4           	-2  	0.125	        0.375
    # 0.25	0.25    	1       	4           	-2  	0.0625	        0.4375
    # 0.25	0.25    	2       	4           	-2  	0	            0.5
    # 0.25	0.25    	3       	4           	-2  	0	            0.5
    # 0.25	0.25    	4       	4           	-2  	0	            0.5
    # 0.25	0.25    	-1      	4           	-2  	0.1875	        0.3125
    # 0.25	0.25    	-2      	4           	-2  	0.25	        0.25
    # 0.25	0.25    	-3      	4           	-2  	0.3125	        0.1875
    # 0.25	0.25    	-4      	4           	-2  	0.375	        0.125
    buy: mango.Order = fake_order(quantity=Decimal("0.25"), side=mango.Side.BUY)
    sell: mango.Order = fake_order(quantity=Decimal("0.25"), side=mango.Side.SELL)
    target: Decimal = Decimal(-2)
    positions: typing.Sequence[int] = [0, 1, 2, 3, 4, -1, -2, -3, -4]
    adjusted_buys: typing.Sequence[Decimal] = [
        Decimal("0.125"),
        Decimal("0.0625"),
        Decimal(0),
        Decimal(0),
        Decimal(0),
        Decimal("0.1875"),
        Decimal("0.25"),
        Decimal("0.3125"),
        Decimal("0.375"),
    ]
    adjusted_sells: typing.Sequence[Decimal] = [
        Decimal("0.375"),
        Decimal("0.4375"),
        Decimal("0.5"),
        Decimal("0.5"),
        Decimal("0.5"),
        Decimal("0.3125"),
        Decimal("0.25"),
        Decimal("0.1875"),
        Decimal("0.125"),
    ]
    for index, position in enumerate(positions):
        buy_quantity, sell_quantity = __biasquantityonposition_pair(
            BQOPInput(buy, sell, Decimal(position), target, Decimal(4))
        )
        assert buy_quantity == adjusted_buys[index]
        assert sell_quantity == adjusted_sells[index]


def test_table_fractional_positive_target() -> None:
    # This table is taken from the docs/BiasQuantityOnPosition.ods spreadsheet.
    #
    # BUY	SELL	POSITION	MAX POSITION	TARGET	ADJUSTED BUY	ADJUSTED SELL
    # 0.25	0.25    	0       	4           	2   	0.375       	0.125
    # 0.25	0.25    	1       	4           	2   	0.3125      	0.1875
    # 0.25	0.25    	2       	4           	2   	0.25        	0.25
    # 0.25	0.25    	3       	4           	2   	0.1875      	0.3125
    # 0.25	0.25    	4       	4           	2   	0.125       	0.375
    # 0.25	0.25    	-1      	4           	2   	0.4375      	0.0625
    # 0.25	0.25    	-2      	4           	2   	0.5     	    0
    # 0.25	0.25    	-3      	4           	2   	0.5     	    0
    # 0.25	0.25    	-4      	4           	2   	0.5     	    0
    buy: mango.Order = fake_order(quantity=Decimal("0.25"), side=mango.Side.BUY)
    sell: mango.Order = fake_order(quantity=Decimal("0.25"), side=mango.Side.SELL)
    target: Decimal = Decimal(2)
    positions: typing.Sequence[int] = [0, 1, 2, 3, 4, -1, -2, -3, -4]
    adjusted_buys: typing.Sequence[Decimal] = [
        Decimal("0.375"),
        Decimal("0.3125"),
        Decimal("0.25"),
        Decimal("0.1875"),
        Decimal("0.125"),
        Decimal("0.4375"),
        Decimal("0.5"),
        Decimal("0.5"),
        Decimal("0.5"),
    ]
    adjusted_sells: typing.Sequence[Decimal] = [
        Decimal("0.125"),
        Decimal("0.1875"),
        Decimal("0.25"),
        Decimal("0.3125"),
        Decimal("0.375"),
        Decimal("0.0625"),
        Decimal("0"),
        Decimal("0"),
        Decimal("0"),
    ]
    for index, position in enumerate(positions):
        buy_quantity, sell_quantity = __biasquantityonposition_pair(
            BQOPInput(buy, sell, Decimal(position), target, Decimal(4))
        )
        assert buy_quantity == adjusted_buys[index]
        assert sell_quantity == adjusted_sells[index]
