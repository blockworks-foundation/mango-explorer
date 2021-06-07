from .context import mango
from .fakes import fake_context

from decimal import Decimal


def test_constructor():
    context: mango.Context = fake_context()
    account_liquidator: mango.AccountLiquidator = mango.NullAccountLiquidator()
    wallet_balancer: mango.WalletBalancer = mango.NullWalletBalancer()
    worthwhile_threshold: Decimal = Decimal("0.1")
    actual = mango.LiquidationProcessor(context, account_liquidator, wallet_balancer, worthwhile_threshold)
    assert actual is not None
    assert actual.logger is not None
    assert actual.context == context
    assert actual.account_liquidator == account_liquidator
    assert actual.wallet_balancer == wallet_balancer
    assert actual.worthwhile_threshold == worthwhile_threshold
