# from .context import mango
# from .mocks import mock_group, mock_prices, mock_margin_account, mock_open_orders

# import typing

# from decimal import Decimal


# def test_constructor():
#     group = mock_group()
#     prices = mock_prices(["2000", "30000", "40", "5", "1"])
#     deposits = ["0", "0", "0", "0", "1000"]
#     borrows = ["0", "0", "0", "0", "0"]
#     margin_account = mock_margin_account(group, deposits, borrows, [])
#     balance_sheet = margin_account.get_balance_sheet_totals(group, prices)
#     balances = margin_account.get_intrinsic_balances(group)
#     state = mango.LiquidatableState.RIPE | mango.LiquidatableState.LIQUIDATABLE | mango.LiquidatableState.ABOVE_WATER
#     worthwhile_threshold = Decimal(1)
#     actual = mango.LiquidatableReport(group, prices, margin_account, balance_sheet,
#                                       balances, state, worthwhile_threshold)

#     assert actual is not None
#     assert actual.logger is not None
#     assert actual.balance_sheet == balance_sheet
#     assert actual.balances == balances
#     assert actual.state != mango.LiquidatableState.UNSET
#     assert actual.state & mango.LiquidatableState.RIPE
#     assert actual.state & mango.LiquidatableState.LIQUIDATABLE
#     assert actual.state & mango.LiquidatableState.ABOVE_WATER
#     assert not (actual.state & mango.LiquidatableState.WORTHWHILE)
#     assert actual.worthwhile_threshold == worthwhile_threshold


# def test_non_ripe_account_no_openorders():
#     group = mock_group()
#     prices = mock_prices(["2000", "30000", "40", "5", "1"])
#     deposits = ["0", "0", "0", "0", "1000"]
#     borrows = ["0", "0", "0", "0", "0"]
#     margin_account = mock_margin_account(group, deposits, borrows, [])
#     worthwhile_threshold = Decimal("0.01")

#     actual = mango.LiquidatableReport.build(group, prices, margin_account, worthwhile_threshold)
#     assert actual.state == mango.LiquidatableState.UNSET
#     assert not (actual.state & mango.LiquidatableState.RIPE)
#     assert not (actual.state & mango.LiquidatableState.LIQUIDATABLE)
#     assert not (actual.state & mango.LiquidatableState.ABOVE_WATER)
#     assert not (actual.state & mango.LiquidatableState.WORTHWHILE)


# def test_ripe_account_no_openorders():
#     group = mock_group()
#     prices = mock_prices(["2000", "30000", "40", "5", "1"])
#     deposits = ["0", "0", "0", "0", "1000"]

#     # 170 @ 5 = 850 for a collateral ratio of 1000/850 = 117% - ripe but not liquidatable
#     borrows = ["0", "0", "0", "170", "0"]

#     margin_account = mock_margin_account(group, deposits, borrows, [])
#     worthwhile_threshold = Decimal("0.01")

#     actual = mango.LiquidatableReport.build(group, prices, margin_account, worthwhile_threshold)
#     assert actual.state != mango.LiquidatableState.UNSET
#     assert actual.state & mango.LiquidatableState.RIPE
#     assert not (actual.state & mango.LiquidatableState.LIQUIDATABLE)
#     assert actual.state & mango.LiquidatableState.ABOVE_WATER
#     assert actual.state & mango.LiquidatableState.WORTHWHILE


# def test_liquidatable_account_no_openorders():
#     group = mock_group()
#     prices = mock_prices(["2000", "30000", "40", "5", "1"])
#     deposits = ["0", "0", "0", "0", "1000"]

#     # 200 @ 5 = 1000 for a collateral ratio of 1000/1000 = 100% - liquidatable but not above water
#     borrows = ["0", "0", "0", "200", "0"]

#     margin_account = mock_margin_account(group, deposits, borrows, [])
#     worthwhile_threshold = Decimal("0.01")

#     actual = mango.LiquidatableReport.build(group, prices, margin_account, worthwhile_threshold)
#     assert actual.state != mango.LiquidatableState.UNSET
#     assert actual.state & mango.LiquidatableState.RIPE
#     assert actual.state & mango.LiquidatableState.LIQUIDATABLE
#     assert not (actual.state & mango.LiquidatableState.ABOVE_WATER)
#     assert not (actual.state & mango.LiquidatableState.WORTHWHILE)


# def test_above_water_account_no_openorders():
#     group = mock_group()
#     prices = mock_prices(["2000", "30000", "40", "5", "1"])
#     deposits = ["0", "0", "0", "0", "1000"]

#     # 199.998 @ 5 = 999.99 for a collateral ratio of 1000/999.99 = 100.001% - liquidatable and above
#     # water but not worthwhile because the $0.01 available is not greater than the whorthwhile_threshold.
#     borrows = ["0", "0", "0", "199.998", "0"]

#     margin_account = mock_margin_account(group, deposits, borrows, [])
#     worthwhile_threshold = Decimal("0.01")

#     actual = mango.LiquidatableReport.build(group, prices, margin_account, worthwhile_threshold)
#     assert actual.state != mango.LiquidatableState.UNSET
#     assert actual.state & mango.LiquidatableState.RIPE
#     assert actual.state & mango.LiquidatableState.LIQUIDATABLE
#     assert actual.state & mango.LiquidatableState.ABOVE_WATER
#     assert not (actual.state & mango.LiquidatableState.WORTHWHILE)


# def test_worthwhile_account_no_openorders():
#     group = mock_group()
#     prices = mock_prices(["2000", "30000", "40", "5", "1"])
#     deposits = ["0", "0", "0", "0", "1000"]

#     # 199.99 @ 5 = 999.95 for a collateral ratio of 1000/999.99 = 100.005% - liquidatable, above water
#     # and worthwhile because the $0.05 available is greater than the whorthwhile_threshold.
#     borrows = ["0", "0", "0", "199.99", "0"]

#     margin_account = mock_margin_account(group, deposits, borrows, [])
#     worthwhile_threshold = Decimal("0.01")

#     actual = mango.LiquidatableReport.build(group, prices, margin_account, worthwhile_threshold)
#     assert actual.state != mango.LiquidatableState.UNSET
#     assert actual.state & mango.LiquidatableState.RIPE
#     assert actual.state & mango.LiquidatableState.LIQUIDATABLE
#     assert actual.state & mango.LiquidatableState.ABOVE_WATER
#     assert actual.state & mango.LiquidatableState.WORTHWHILE


# def test_non_ripe_account_openorders_base():
#     group = mock_group()
#     prices = mock_prices(["2000", "30000", "40", "5", "1"])
#     deposits = ["0", "0", "0", "0", "1000"]
#     borrows = ["0", "0", "0", "100", "0"]
#     open_orders: typing.Sequence[mango.OpenOrders] = [None,
#                                                   None,
#                                                   None,
#                                                   mock_open_orders(base_token_total=Decimal(0)),
#                                                   None]
#     margin_account = mock_margin_account(group, deposits, borrows, open_orders)
#     worthwhile_threshold = Decimal("0.01")

#     actual = mango.LiquidatableReport.build(group, prices, margin_account, worthwhile_threshold)
#     assert actual.state != mango.LiquidatableState.UNSET
#     assert not (actual.state & mango.LiquidatableState.RIPE)
#     assert not (actual.state & mango.LiquidatableState.LIQUIDATABLE)
#     assert actual.state & mango.LiquidatableState.ABOVE_WATER
#     assert actual.state & mango.LiquidatableState.WORTHWHILE


# # The idea of these OpenOrders tests is that the deposits and borrows remain the same and the only
# # differences are through changes in OpenOrders balances.

# def test_ripe_account_openorders_base():
#     group = mock_group()
#     prices = mock_prices(["2000", "30000", "40", "5", "1"])
#     deposits = ["0", "0", "0", "0", "900"]
#     borrows = ["0", "0", "0", "200", "0"]

#     # 1150/1000 = 115% - ripe but not liquidatable
#     open_orders: typing.Sequence[mango.OpenOrders] = [None,
#                                                   None,
#                                                   None,
#                                                   mock_open_orders(base_token_total=Decimal(50)),
#                                                   None
#                                                   ]
#     margin_account = mock_margin_account(group, deposits, borrows, open_orders)
#     worthwhile_threshold = Decimal("0.01")

#     actual = mango.LiquidatableReport.build(group, prices, margin_account, worthwhile_threshold)
#     assert actual.state != mango.LiquidatableState.UNSET
#     assert actual.state & mango.LiquidatableState.RIPE
#     assert not (actual.state & mango.LiquidatableState.LIQUIDATABLE)
#     assert actual.state & mango.LiquidatableState.ABOVE_WATER
#     assert actual.state & mango.LiquidatableState.WORTHWHILE


# def test_liquidatable_account_openorders_base():
#     group = mock_group()
#     prices = mock_prices(["2000", "30000", "40", "5", "1"])
#     deposits = ["0", "0", "0", "0", "900"]
#     borrows = ["0", "0", "0", "200", "0"]

#     # 200 @ 5 = 1000 for a collateral ratio of 1000/1000 = 100% - liquidatable but not above water
#     open_orders: typing.Sequence[mango.OpenOrders] = [None,
#                                                   None,
#                                                   None,
#                                                   mock_open_orders(base_token_total=Decimal(20)),
#                                                   None]
#     margin_account = mock_margin_account(group, deposits, borrows, open_orders)
#     worthwhile_threshold = Decimal("0.01")

#     actual = mango.LiquidatableReport.build(group, prices, margin_account, worthwhile_threshold)
#     assert actual.state != mango.LiquidatableState.UNSET
#     assert actual.state & mango.LiquidatableState.RIPE
#     assert actual.state & mango.LiquidatableState.LIQUIDATABLE
#     assert not (actual.state & mango.LiquidatableState.ABOVE_WATER)
#     assert not (actual.state & mango.LiquidatableState.WORTHWHILE)


# def test_above_water_account_openorders_base():
#     group = mock_group()
#     prices = mock_prices(["2000", "30000", "40", "5", "1"])
#     deposits = ["0", "0", "0", "0", "900"]
#     borrows = ["0", "0", "0", "200", "0"]

#     # 900 + (20.002 @ 5) = 1000.01 for a collateral ratio of 1000.01/1000 = 100.001% - liquidatable and above
#     # water but not worthwhile because the $0.01 available is not greater than the whorthwhile_threshold.
#     open_orders: typing.Sequence[mango.OpenOrders] = [None,
#                                                   None,
#                                                   None,
#                                                   mock_open_orders(base_token_total=Decimal("20.002")),
#                                                   None]
#     margin_account = mock_margin_account(group, deposits, borrows, open_orders)
#     worthwhile_threshold = Decimal("0.01")

#     actual = mango.LiquidatableReport.build(group, prices, margin_account, worthwhile_threshold)
#     assert actual.state != mango.LiquidatableState.UNSET
#     assert actual.state & mango.LiquidatableState.RIPE
#     assert actual.state & mango.LiquidatableState.LIQUIDATABLE
#     assert actual.state & mango.LiquidatableState.ABOVE_WATER
#     assert not (actual.state & mango.LiquidatableState.WORTHWHILE)


# def test_worthwhile_account_openorders_base():
#     group = mock_group()
#     prices = mock_prices(["2000", "30000", "40", "5", "1"])
#     deposits = ["0", "0", "0", "0", "900"]
#     borrows = ["0", "0", "0", "200", "0"]

#     # 900 + (20.003 @ 5) = 1000.015 for a collateral ratio of 1000.015/1000 = 100.0015% - liquidatable, above water
#     # and worthwhile because the $0.015 available is greater than the whorthwhile_threshold.
#     open_orders: typing.Sequence[mango.OpenOrders] = [None,
#                                                   None,
#                                                   None,
#                                                   mock_open_orders(base_token_total=Decimal("20.003")),
#                                                   None]

#     margin_account = mock_margin_account(group, deposits, borrows, open_orders)
#     worthwhile_threshold = Decimal("0.01")

#     actual = mango.LiquidatableReport.build(group, prices, margin_account, worthwhile_threshold)
#     assert actual.state != mango.LiquidatableState.UNSET
#     assert actual.state & mango.LiquidatableState.RIPE
#     assert actual.state & mango.LiquidatableState.LIQUIDATABLE
#     assert actual.state & mango.LiquidatableState.ABOVE_WATER
#     assert actual.state & mango.LiquidatableState.WORTHWHILE


# def test_non_ripe_account_openorders_quote():
#     group = mock_group()
#     prices = mock_prices(["2000", "30000", "40", "5", "1"])
#     deposits = ["0", "0", "0", "0", "1000"]
#     borrows = ["0", "0", "0", "100", "0"]
#     open_orders: typing.Sequence[mango.OpenOrders] = [None,
#                                                   None,
#                                                   None,
#                                                   mock_open_orders(quote_token_total=Decimal(0)),
#                                                   None]
#     margin_account = mock_margin_account(group, deposits, borrows, open_orders)
#     worthwhile_threshold = Decimal("0.01")

#     actual = mango.LiquidatableReport.build(group, prices, margin_account, worthwhile_threshold)
#     assert actual.state != mango.LiquidatableState.UNSET
#     assert not (actual.state & mango.LiquidatableState.RIPE)
#     assert not (actual.state & mango.LiquidatableState.LIQUIDATABLE)
#     assert actual.state & mango.LiquidatableState.ABOVE_WATER
#     assert actual.state & mango.LiquidatableState.WORTHWHILE


# # The idea of these OpenOrders tests is that the deposits and borrows remain the same and the only
# # differences are through changes in OpenOrders balances.

# def test_ripe_account_openorders_quote():
#     group = mock_group()
#     prices = mock_prices(["2000", "30000", "40", "5", "1"])
#     deposits = ["0", "0", "0", "0", "900"]
#     borrows = ["0", "0", "0", "200", "0"]

#     # 1150/1000 = 115% - ripe but not liquidatable
#     open_orders: typing.Sequence[mango.OpenOrders] = [None,
#                                                   None,
#                                                   None,
#                                                   mock_open_orders(quote_token_total=Decimal(250)),
#                                                   None
#                                                   ]
#     margin_account = mock_margin_account(group, deposits, borrows, open_orders)
#     worthwhile_threshold = Decimal("0.01")

#     actual = mango.LiquidatableReport.build(group, prices, margin_account, worthwhile_threshold)
#     assert actual.state != mango.LiquidatableState.UNSET
#     assert actual.state & mango.LiquidatableState.RIPE
#     assert not (actual.state & mango.LiquidatableState.LIQUIDATABLE)
#     assert actual.state & mango.LiquidatableState.ABOVE_WATER
#     assert actual.state & mango.LiquidatableState.WORTHWHILE


# def test_liquidatable_account_openorders_quote():
#     group = mock_group()
#     prices = mock_prices(["2000", "30000", "40", "5", "1"])
#     deposits = ["0", "0", "0", "0", "900"]
#     borrows = ["0", "0", "0", "200", "0"]

#     # 200 @ 5 = 1000 for a collateral ratio of 1000/1000 = 100% - liquidatable but not above water
#     open_orders: typing.Sequence[mango.OpenOrders] = [None,
#                                                   None,
#                                                   None,
#                                                   mock_open_orders(quote_token_total=Decimal(100)),
#                                                   None]
#     margin_account = mock_margin_account(group, deposits, borrows, open_orders)
#     worthwhile_threshold = Decimal("0.01")

#     actual = mango.LiquidatableReport.build(group, prices, margin_account, worthwhile_threshold)
#     assert actual.state != mango.LiquidatableState.UNSET
#     assert actual.state & mango.LiquidatableState.RIPE
#     assert actual.state & mango.LiquidatableState.LIQUIDATABLE
#     assert not (actual.state & mango.LiquidatableState.ABOVE_WATER)
#     assert not (actual.state & mango.LiquidatableState.WORTHWHILE)


# def test_above_water_account_openorders_quote():
#     group = mock_group()
#     prices = mock_prices(["2000", "30000", "40", "5", "1"])
#     deposits = ["0", "0", "0", "0", "900"]
#     borrows = ["0", "0", "0", "200", "0"]

#     # 900 + 100.01 for a collateral ratio of 1000.01/1000 = 100.001% - liquidatable and above
#     # water but not worthwhile because the $0.01 available is not greater than the whorthwhile_threshold.
#     open_orders: typing.Sequence[mango.OpenOrders] = [None,
#                                                   None,
#                                                   None,
#                                                   mock_open_orders(quote_token_total=Decimal("100.01")),
#                                                   None]
#     margin_account = mock_margin_account(group, deposits, borrows, open_orders)
#     worthwhile_threshold = Decimal("0.01")

#     actual = mango.LiquidatableReport.build(group, prices, margin_account, worthwhile_threshold)
#     assert actual.state != mango.LiquidatableState.UNSET
#     assert actual.state & mango.LiquidatableState.RIPE
#     assert actual.state & mango.LiquidatableState.LIQUIDATABLE
#     assert actual.state & mango.LiquidatableState.ABOVE_WATER
#     assert not (actual.state & mango.LiquidatableState.WORTHWHILE)


# def test_worthwhile_account_openorders_quote():
#     group = mock_group()
#     prices = mock_prices(["2000", "30000", "40", "5", "1"])
#     deposits = ["0", "0", "0", "0", "900"]
#     borrows = ["0", "0", "0", "200", "0"]

#     # 199.99 @ 5 = 999.95 for a collateral ratio of 1000/999.99 = 100.005% - liquidatable, above water
#     # and worthwhile because the $0.05 available is greater than the whorthwhile_threshold.
#     open_orders: typing.Sequence[mango.OpenOrders] = [None,
#                                                   None,
#                                                   None,
#                                                   mock_open_orders(quote_token_total=Decimal(101)),
#                                                   None]

#     margin_account = mock_margin_account(group, deposits, borrows, open_orders)
#     worthwhile_threshold = Decimal("0.01")

#     actual = mango.LiquidatableReport.build(group, prices, margin_account, worthwhile_threshold)
#     assert actual.state != mango.LiquidatableState.UNSET
#     assert actual.state & mango.LiquidatableState.RIPE
#     assert actual.state & mango.LiquidatableState.LIQUIDATABLE
#     assert actual.state & mango.LiquidatableState.ABOVE_WATER
#     assert actual.state & mango.LiquidatableState.WORTHWHILE


# def test_liquidatable_account_referrer_fee():
#     group = mock_group()
#     prices = mock_prices(["2000", "30000", "40", "5", "1"])
#     deposits = ["0", "0", "0", "0", "900"]
#     borrows = ["0", "0", "0", "200", "0"]

#     # 200 @ 5 = 1000 for a collateral ratio of 1000/1000 = 100% - liquidatable but not above water
#     open_orders: typing.Sequence[mango.OpenOrders] = [None,
#                                                   None,
#                                                   None,
#                                                   mock_open_orders(quote_token_total=Decimal(100)),
#                                                   None]
#     margin_account = mock_margin_account(group, deposits, borrows, open_orders)
#     worthwhile_threshold = Decimal("0.01")

#     actual = mango.LiquidatableReport.build(group, prices, margin_account, worthwhile_threshold)
#     assert actual.state != mango.LiquidatableState.UNSET
#     assert actual.state & mango.LiquidatableState.RIPE
#     assert actual.state & mango.LiquidatableState.LIQUIDATABLE
#     assert not (actual.state & mango.LiquidatableState.ABOVE_WATER)
#     assert not (actual.state & mango.LiquidatableState.WORTHWHILE)

#     # Exactly the same scenario as above, but with referrer_rebate_accrued=Decimal(1) in one OpenOrders.
#     # This gives a collateral ratio of 1.001, which is ripe, liquidatable, above water and worthwhile.
#     open_orders: typing.Sequence[mango.OpenOrders] = [None,
#                                                   None,
#                                                   None,
#                                                   mock_open_orders(quote_token_total=Decimal(100),
#                                                                    referrer_rebate_accrued=Decimal(1)),
#                                                   None]
#     margin_account = mock_margin_account(group, deposits, borrows, open_orders)
#     worthwhile_threshold = Decimal("0.01")

#     actual = mango.LiquidatableReport.build(group, prices, margin_account, worthwhile_threshold)
#     assert actual.state != mango.LiquidatableState.UNSET
#     assert actual.state & mango.LiquidatableState.RIPE
#     assert actual.state & mango.LiquidatableState.LIQUIDATABLE
#     assert actual.state & mango.LiquidatableState.ABOVE_WATER
#     assert actual.state & mango.LiquidatableState.WORTHWHILE
