from .context import mango
from .fakes import fake_account_info, fake_seeded_public_key

from decimal import Decimal
from mango.layouts import layouts


def test_construction():
    account_info = fake_account_info()
    meta_data = mango.Metadata(layouts.DATA_TYPE.Group, mango.Version.V1, True)
    group = fake_seeded_public_key("group")
    owner = fake_seeded_public_key("owner")
    in_basket = [Decimal(1), Decimal(0), Decimal(3)]
    deposits = [Decimal(10), Decimal(0), Decimal(5)]
    borrows = [Decimal(0), Decimal(0), Decimal(0)]
    net_assets = [Decimal(10), Decimal(0), Decimal(5)]
    spot_open_orders = [fake_seeded_public_key("spot1"), fake_seeded_public_key(
        "spot2"), fake_seeded_public_key("spot3")]
    is_bankrupt = False

    # TODO - this isn't right.
    perp_accounts = [fake_seeded_public_key("perp1"), fake_seeded_public_key("perp2"), fake_seeded_public_key("perp3")]

    actual = mango.Account(account_info, mango.Version.V1, meta_data, group, owner, in_basket,
                           deposits, borrows, net_assets, spot_open_orders, perp_accounts, is_bankrupt)

    assert actual is not None
    assert actual.logger is not None
    assert actual.version == mango.Version.V1
    assert actual.meta_data == meta_data
    assert actual.group == group
    assert actual.owner == owner
    assert actual.in_basket == in_basket
    assert actual.deposits == deposits
    assert actual.borrows == borrows
    assert actual.net_assets == net_assets
    assert actual.spot_open_orders == spot_open_orders
    assert actual.perp_accounts == perp_accounts
