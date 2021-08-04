from .context import mango
from .fakes import fake_account_info, fake_seeded_public_key, fake_token_info, fake_token_value

from decimal import Decimal
from mango.layouts import layouts


def test_construction():
    account_info = fake_account_info()
    meta_data = mango.Metadata(layouts.DATA_TYPE.Group, mango.Version.V1, True)
    group = fake_seeded_public_key("group")
    owner = fake_seeded_public_key("owner")
    in_margin_basket = [False, True, False, True, True]
    quote_deposit = fake_token_value(Decimal(50))
    quote_borrow = fake_token_value(Decimal(5))
    quote = mango.AccountBasketToken(fake_token_info(), quote_deposit, quote_borrow)
    deposit1 = fake_token_value(Decimal(1))
    deposit2 = fake_token_value(Decimal(2))
    deposit3 = fake_token_value(Decimal(3))
    borrow1 = fake_token_value(Decimal("0.1"))
    borrow2 = fake_token_value(Decimal("0.2"))
    borrow3 = fake_token_value(Decimal("0.3"))
    basket = [
        mango.AccountBasketBaseToken(fake_token_info(), deposit1, borrow1,
                                     fake_seeded_public_key("spot openorders 1"), fake_seeded_public_key("perp1")),
        mango.AccountBasketBaseToken(fake_token_info(), deposit2, borrow2,
                                     fake_seeded_public_key("spot openorders 2"), fake_seeded_public_key("perp2")),
        mango.AccountBasketBaseToken(fake_token_info(), deposit3, borrow3,
                                     fake_seeded_public_key("spot openorders 3"), fake_seeded_public_key("perp3")),
    ]
    msrm_amount = Decimal(0)
    being_liquidated = False
    is_bankrupt = False

    actual = mango.Account(account_info, mango.Version.V1, meta_data, group, owner, quote,
                           in_margin_basket, basket, msrm_amount, being_liquidated, is_bankrupt)

    assert actual is not None
    assert actual.logger is not None
    assert actual.version == mango.Version.V1
    assert actual.meta_data == meta_data
    assert actual.group == group
    assert actual.owner == owner
    assert actual.basket_indices == in_margin_basket
    assert actual.deposits == [None, deposit1, None, deposit2, deposit3, quote_deposit]
    assert actual.borrows == [None, borrow1, None, borrow2, borrow3, quote_borrow]
    assert actual.net_assets == [None, deposit1 - borrow1, None,
                                 deposit2 - borrow2, deposit3 - borrow3, quote_deposit - quote_borrow]
    assert actual.spot_open_orders == [None, fake_seeded_public_key("spot openorders 1"), None, fake_seeded_public_key(
        "spot openorders 2"), fake_seeded_public_key("spot openorders 3")]
    assert actual.perp_accounts == [None, fake_seeded_public_key("perp1"), None, fake_seeded_public_key(
        "perp2"), fake_seeded_public_key("perp3")]
    assert actual.msrm_amount == msrm_amount
    assert actual.being_liquidated == being_liquidated
    assert actual.is_bankrupt == is_bankrupt
