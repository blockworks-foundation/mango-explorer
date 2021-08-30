from .context import mango
from .fakes import fake_context
# from .mocks import mock_group, mock_prices, mock_open_orders

# import typing

from decimal import Decimal


def test_constructor():
    context: mango.Context = fake_context()
    name: str = "Test Liquidator"
    account_liquidator: mango.AccountLiquidator = mango.NullAccountLiquidator()
    wallet_balancer: mango.WalletBalancer = mango.NullWalletBalancer()
    worthwhile_threshold: Decimal = Decimal("0.1")
    actual = mango.LiquidationProcessor(context, name, account_liquidator, wallet_balancer, worthwhile_threshold)
    assert actual is not None
    assert actual.logger is not None
    assert actual.context == context
    assert actual.account_liquidator == account_liquidator
    assert actual.wallet_balancer == wallet_balancer
    assert actual.worthwhile_threshold == worthwhile_threshold


#
# Testing whether an account is liquidatable should be simpler, and it could be made
# simpler. But we want our test paths to follow the paths used in the actual Liquidator
# code, and we also want that Liquidator code to be 'progressive', showing A ripe
# accounts, B of those A are undercollateralised, C of those B are above water and D of
# those C are worth liquidating. That rules out a simple 'is liquidatable' property.
#
# So that means a lot of additional code is required to set up the tests. Most of the
# additional code is common and shared across test functions.
#

# class LiquidateMock:
#     def __init__(self, liquidation_processor: mango.LiquidationProcessor):
#         self.liquidation_processor = liquidation_processor
#         self.captured_group: typing.Optional[mango.Group] = None
#         self.captured_prices: typing.Optional[typing.Sequence[mango.TokenValue]] = None
#         self.captured_to_liquidate: typing.Optional[typing.Sequence[mango.LiquidatableReport]] = None

#         # This monkeypatch is a bit nasty. It would be better to make the LiquidationProcessor
#         # a bit more test-friendly.
#         liquidation_processor._liquidate_all = self.liquidate_capture  # type: ignore

#     def liquidate_capture(self, group: mango.Group, prices: typing.Sequence[mango.TokenValue], to_liquidate: typing.Sequence[mango.LiquidatableReport]):
#         self.captured_group = group
#         self.captured_prices = prices
#         self.captured_to_liquidate = to_liquidate


# def capturing_liquidation_processor() -> LiquidateMock:
#     context: mango.Context = fake_context()
#     name: str = "Test Liquidator"
#     account_liquidator: mango.AccountLiquidator = mango.NullAccountLiquidator()
#     wallet_balancer: mango.WalletBalancer = mango.NullWalletBalancer()
#     worthwhile_threshold: Decimal = Decimal("0.1")
#     actual = mango.LiquidationProcessor(context, name, account_liquidator, wallet_balancer, worthwhile_threshold)

#     return LiquidateMock(actual)


# def validate_liquidation_results(deposits: typing.Sequence[str], borrows: typing.Sequence[str], openorders: typing.Sequence[typing.Optional[mango.OpenOrders]], price_iterations: typing.Sequence[typing.Tuple[typing.Sequence[str], str, bool]]):
#     group = mock_group()
#     capturer = capturing_liquidation_processor()
#     margin_account = mock_margin_account(group,
#                                          deposits,
#                                          borrows,
#                                          openorders)
#     for (prices, calculated_balance, liquidatable) in price_iterations:
#         token_prices = mock_prices(prices)
#         balance_sheet = margin_account.get_balance_sheet_totals(group, token_prices)
#         assert balance_sheet.assets - balance_sheet.liabilities == Decimal(calculated_balance)

#         capturer.liquidation_processor.update_margin_accounts([margin_account])
#         capturer.liquidation_processor.update_prices(group, token_prices)

#         if liquidatable:
#             assert (capturer.captured_to_liquidate is not None) and (len(capturer.captured_to_liquidate) == 1)
#             assert capturer.captured_to_liquidate[0].margin_account == margin_account
#         else:
#             assert (capturer.captured_to_liquidate is not None) and (len(capturer.captured_to_liquidate) == 0)


# def test_non_liquidatable_account():
#     # A simple case - no borrows
#     validate_liquidation_results(
#         ["0", "0", "0", "0", "1000"],
#         ["0", "0", "0", "0", "0"],
#         [None, None, None, None, None],
#         [
#             (
#                 ["2000", "30000", "40", "5", "1"],
#                 "1000",
#                 False
#             )
#         ]
#     )


# def test_liquidatable_account():
#     # A simple case with no currency conversions - 1000 USDC and (somehow) borrowing
#     # 950 USDC
#     validate_liquidation_results(
#         ["0", "0", "0", "0", "1000"],
#         ["0", "0", "0", "0", "950"],
#         [None, None, None, None, None],
#         [
#             (
#                 ["2000", "30000", "40", "5", "1"],
#                 "50",
#                 True
#             )
#         ]
#     )


# def test_converted_balance_not_liquidatable():
#     # A more realistic case. 1000 USDC, borrowed 180 SRM now @ 5 USDC
#     validate_liquidation_results(
#         ["0", "0", "0", "0", "1000"],
#         ["0", "0", "0", "180", "0"],
#         [None, None, None, None, None],
#         [
#             (
#                 ["2000", "30000", "40", "5", "1"],
#                 "100",
#                 False
#             )
#         ]
#     )


# def test_converted_balance_liquidatable():
#     # 1000 USDC, borrowed 190 SRM now @ 5 USDC
#     validate_liquidation_results(
#         ["0", "0", "0", "0", "1000"],
#         ["0", "0", "0", "190", "0"],
#         [None, None, None, None, None],
#         [
#             (
#                 ["2000", "30000", "40", "5", "1"],
#                 "50",
#                 True
#             )
#         ]
#     )


# def test_converted_balance_not_liquidatable_becomes_liquidatable_on_price_change():
#     # 1000 USDC, borrowed 180 SRM @ 5 USDC, price goes to 5.2 USDC
#     validate_liquidation_results(
#         ["0", "0", "0", "0", "1000"],
#         ["0", "0", "0", "180", "0"],
#         [None, None, None, None, None],
#         [
#             (
#                 ["2000", "30000", "40", "5", "1"],
#                 "100",
#                 False
#             ),
#             (
#                 ["2000", "30000", "40", "5.2", "1"],
#                 "64",
#                 True
#             )
#         ]
#     )


# def test_converted_balance_liquidatable_becomes_not_liquidatable_on_price_change():
#     # 1000 USDC, borrowed 180 SRM, price goes to 5.2 USDC (and account becomes liquidatable),
#     # then SRM price falls to 5 USDC (and account becomes non-liqudatable). Can margin
#     # accounts switch from liquidatable (but not liquidated) to non-liquidatable? Yes - if
#     # something causes an error on the liquidation attempt, it's skipped until the next
#     # round (with fresh prices). If no-one else tries to liquidate it (unlikely), it'll
#     # appear in the next round as non-liquidatable.
#     validate_liquidation_results(
#         ["0", "0", "0", "0", "1000"],
#         ["0", "0", "0", "180", "0"],
#         [None, None, None, None, None],
#         [
#             (
#                 ["2000", "30000", "40", "5.2", "1"],
#                 "64",
#                 True
#             ),
#             (
#                 ["2000", "30000", "40", "5", "1"],
#                 "100",
#                 False
#             )
#         ]
#     )


# def test_open_orders_balance_not_liquidatable():
#     # SRM OO account has 10 SRM in it
#     validate_liquidation_results(
#         ["0", "0", "0", "0", "1000"],
#         ["0", "0", "0", "190", "0"],
#         [None, None, None, mock_open_orders(base_token_total=Decimal(10)), None],
#         [
#             (
#                 ["2000", "30000", "40", "5", "1"],
#                 "100",
#                 False
#             )
#         ]
#     )


# def test_open_orders_balance_liquidatable():
#     # SRM OO account has only 9 SRM in it.
#     # Assets (1045) / Liabiities (950) = collateral ratio of exactly 1.1
#     validate_liquidation_results(
#         ["0", "0", "0", "0", "1000"],
#         ["0", "0", "0", "190", "0"],
#         [None, None, None, mock_open_orders(base_token_total=Decimal(9)), None],
#         [
#             (
#                 ["2000", "30000", "40", "5", "1"],
#                 "95",
#                 True
#             )
#         ]
#     )


# def test_open_orders_referral_fee_not_liquidatable():
#     # Figures are exactly the same as the test_open_orders_balance_liquidatable() test above,
#     # except for the referrer_rebate_accrued value. If it's not taken into account, the
#     # margin account is liquidatable.
#     validate_liquidation_results(
#         ["0", "0", "0", "0", "1000"],
#         ["0", "0", "0", "190", "0"],
#         [None, None, None, mock_open_orders(base_token_total=Decimal(9), referrer_rebate_accrued=Decimal("0.1")), None],
#         [
#             (
#                 ["2000", "30000", "40", "5", "1"],
#                 "95.1",  # The 0.1 referrer rebate is the difference between non-liquidation and iquidation.
#                 False
#             )
#         ]
#     )


# def test_open_orders_bigger_referral_fee_not_liquidatable():
#     # 900 USDC + 100.1 USDC referrer rebate should be equivalent to the above
#     # test_open_orders_referral_fee_not_liquidatable test.
#     validate_liquidation_results(
#         ["0", "0", "0", "0", "900"],
#         ["0", "0", "0", "190", "0"],
#         [None, None, None, mock_open_orders(base_token_total=Decimal(
#             9), referrer_rebate_accrued=Decimal("100.1")), None],
#         [
#             (
#                 ["2000", "30000", "40", "5", "1"],
#                 "95.1",  # 0.1 of the referrer rebate is the difference between non-liquidation and iquidation.
#                 False
#             )
#         ]
#     )


# def test_open_orders_bigger_referral_fee_liquidatable():
#     # 900 USDC + 100.1 USDC referrer rebate should be equivalent to the above
#     # test_open_orders_referral_fee_not_liquidatable test.
#     validate_liquidation_results(
#         ["0", "0", "0", "0", "900"],
#         ["0", "0", "0", "190", "0"],
#         [None, None, None, mock_open_orders(base_token_total=Decimal(
#             9), referrer_rebate_accrued=Decimal("100")), None],
#         [
#             (
#                 ["2000", "30000", "40", "5", "1"],
#                 "95",  # Just 0.1 more in the referrer rebate would make it non-liquidatable.
#                 True
#             )
#         ]
#     )
