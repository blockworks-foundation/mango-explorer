from .context import mango


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
