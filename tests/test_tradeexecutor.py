from .context import mango
from .fakes import fake_context

from decimal import Decimal


def test_trade_executor_constructor():
    succeeded = False
    try:
        mango.TradeExecutor()
    except TypeError:
        # Can't instantiate the abstract base class.
        succeeded = True
    assert succeeded


def test_null_trade_executor_constructor():
    def reporter(x):
        return None
    actual = mango.NullTradeExecutor(reporter)
    assert actual is not None
    assert actual.logger is not None
    assert actual.reporter == reporter


def test_serum_trade_executor_constructor():
    context: mango.Context = fake_context()
    wallet: mango.Wallet = {"fake": "Wallet"}
    spot_market_lookup: mango.SpotMarketLookup = mango.SpotMarketLookup.default_lookups()
    price_adjustment_factor: Decimal = Decimal(0.05)

    def reporter(x):
        return None
    actual = mango.SerumImmediateTradeExecutor(context, wallet, spot_market_lookup, price_adjustment_factor, reporter)
    assert actual is not None
    assert actual.logger is not None
    assert actual.context == context
    assert actual.wallet == wallet
    assert actual.spot_market_lookup == spot_market_lookup
    assert actual.price_adjustment_factor == price_adjustment_factor
    assert actual.reporter is not None
