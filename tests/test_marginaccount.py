from .context import mango
from .fakes import fake_account_info, fake_seeded_public_key, fake_token

from decimal import Decimal


def test_construction():
    account_flags = mango.MangoAccountFlags(mango.Version.V1, True, False, True, False)
    info = "TestAcc"
    has_borrows = False
    mango_group = fake_seeded_public_key("mango group")
    owner = fake_seeded_public_key("owner")
    being_liquidated = False
    token = fake_token()
    deposits = [mango.TokenValue(token, Decimal(0)), mango.TokenValue(
        token, Decimal(0)), mango.TokenValue(token, Decimal(0))]
    borrows = [mango.TokenValue(token, Decimal(0)), mango.TokenValue(
        token, Decimal(0)), mango.TokenValue(token, Decimal(0))]
    open_orders = [None, None]
    actual = mango.MarginAccount(fake_account_info(), mango.Version.V1, account_flags, info,
                                 has_borrows, mango_group, owner, being_liquidated,
                                 deposits, borrows, open_orders)
    assert actual is not None
    assert actual.logger is not None
    assert actual.version == mango.Version.V1
    assert actual.account_flags == account_flags
    assert actual.info == info
    assert actual.has_borrows == has_borrows
    assert actual.mango_group == mango_group
    assert actual.owner == owner
    assert actual.deposits == deposits
    assert actual.borrows == borrows
    assert actual.open_orders == open_orders
