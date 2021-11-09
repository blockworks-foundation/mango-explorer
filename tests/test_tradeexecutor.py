import typing

from .context import mango
from .fakes import fake_context, fake_wallet

from decimal import Decimal


def test_trade_executor_constructor() -> None:
    succeeded = False
    try:
        mango.TradeExecutor()  # type: ignore[abstract]
    except TypeError:
        # Can't instantiate the abstract base class.
        succeeded = True
    assert succeeded


def test_null_trade_executor_constructor() -> None:
    def reporter(x: typing.Any) -> None:
        return None
    actual = mango.NullTradeExecutor(reporter)
    assert actual is not None
    assert actual.logger is not None
    assert actual.reporter == reporter


def test_serum_trade_executor_constructor() -> None:
    context: mango.Context = fake_context()
    wallet: mango.Wallet = fake_wallet()
    price_adjustment_factor: Decimal = Decimal(0.05)

    def reporter(x: typing.Any) -> None:
        return None
    actual = mango.ImmediateTradeExecutor(context, wallet, None, price_adjustment_factor, reporter)
    assert actual is not None
    assert actual.logger is not None
    assert actual.context == context
    assert actual.wallet == wallet
    assert actual.price_adjustment_factor == price_adjustment_factor
    assert actual.reporter is not None
