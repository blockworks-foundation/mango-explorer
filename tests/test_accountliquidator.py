from .context import mango
from .fakes import fake_context


def test_account_liquidator_constructor():
    succeeded = False
    try:
        mango.AccountLiquidator()
    except TypeError:
        # Can't instantiate the abstract base class.
        succeeded = True
    assert succeeded


def test_null_account_liquidator_constructor():
    actual = mango.NullAccountLiquidator()
    assert actual is not None
    assert actual.logger is not None


def test_actual_account_liquidator_constructor():
    context: mango.Context = fake_context()
    wallet: mango.Wallet = {"fake": "Walle"}
    actual = mango.ActualAccountLiquidator(context, wallet)
    assert actual is not None
    assert actual.logger is not None
    assert actual.context == context
    assert actual.wallet == wallet


def test_force_cancel_orders_account_liquidator_constructor():
    context: mango.Context = fake_context()
    wallet: mango.Wallet = {"fake": "Walle"}
    actual = mango.ForceCancelOrdersAccountLiquidator(context, wallet)
    assert actual is not None
    assert actual.logger is not None
    assert actual.context == context
    assert actual.wallet == wallet


def test_reporting_account_liquidator_constructor():
    inner = mango.NullAccountLiquidator()
    context: mango.Context = fake_context()
    wallet: mango.Wallet = {"fake": "Walle"}
    liquidations_publisher: mango.EventSource[mango.LiquidationEvent] = mango.EventSource()
    liquidator_name = "Test"
    actual = mango.ReportingAccountLiquidator(inner, context, wallet, liquidations_publisher, liquidator_name)
    assert actual is not None
    assert actual.logger is not None
    assert actual.inner == inner
    assert actual.context == context
    assert actual.wallet == wallet
    assert actual.liquidations_publisher == liquidations_publisher
    assert actual.liquidator_name == liquidator_name
