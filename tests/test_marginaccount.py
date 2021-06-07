from .context import mango
from .fakes import fake_account_info, fake_seeded_public_key

from decimal import Decimal


def test_construction():
    account_flags = mango.MangoAccountFlags(mango.Version.V1, True, False, True, False)
    has_borrows = False
    mango_group = fake_seeded_public_key("mango group")
    owner = fake_seeded_public_key("owner")
    deposits = [Decimal(0), Decimal(0), Decimal(0)]
    borrows = [Decimal(0), Decimal(0), Decimal(0)]
    open_orders = [None, None]
    actual = mango.MarginAccount(fake_account_info(), mango.Version.V1, account_flags,
                                 has_borrows, mango_group, owner, deposits, borrows,
                                 open_orders)
    assert actual is not None
    assert actual.logger is not None
    assert actual.version == mango.Version.V1
    assert actual.account_flags == account_flags
    assert actual.has_borrows == has_borrows
    assert actual.mango_group == mango_group
    assert actual.owner == owner
    assert actual.deposits == deposits
    assert actual.borrows == borrows
    assert actual.open_orders == open_orders
