from .context import mango
from .fakes import fake_account_info, fake_seeded_public_key, fake_token_info, fake_instrument, fake_instrument_value, fake_perp_account

from decimal import Decimal
from mango.layouts import layouts


def test_construction() -> None:
    account_info = fake_account_info()
    meta_data = mango.Metadata(layouts.DATA_TYPE.Group, mango.Version.V1, True)
    group = fake_seeded_public_key("group")
    owner = fake_seeded_public_key("owner")
    info = "some name"
    in_margin_basket = [False, False, False, False, False]
    active_in_basket = [False, True, False, True, True]
    raw_quote_deposit = Decimal(50)
    quote_deposit = fake_instrument_value(raw_quote_deposit)
    raw_quote_borrow = Decimal(5)
    quote_borrow = fake_instrument_value(raw_quote_borrow)
    quote = mango.AccountSlot(3, fake_instrument(), fake_token_info(), fake_token_info(), raw_quote_deposit,
                              quote_deposit, raw_quote_borrow, quote_borrow, None, None)
    raw_deposit1 = Decimal(1)
    deposit1 = fake_instrument_value(raw_deposit1)
    raw_deposit2 = Decimal(2)
    deposit2 = fake_instrument_value(raw_deposit2)
    raw_deposit3 = Decimal(3)
    deposit3 = fake_instrument_value(raw_deposit3)
    raw_borrow1 = Decimal("0.1")
    borrow1 = fake_instrument_value(raw_borrow1)
    raw_borrow2 = Decimal("0.2")
    borrow2 = fake_instrument_value(raw_borrow2)
    raw_borrow3 = Decimal("0.3")
    borrow3 = fake_instrument_value(raw_borrow3)
    perp1 = fake_perp_account()
    perp2 = fake_perp_account()
    perp3 = fake_perp_account()
    basket = [
        mango.AccountSlot(0, fake_instrument(), fake_token_info(), fake_token_info(), raw_deposit1, deposit1,
                          raw_borrow1, borrow1, fake_seeded_public_key("spot openorders 1"), perp1),
        mango.AccountSlot(1, fake_instrument(), fake_token_info(), fake_token_info(), raw_deposit2, deposit2,
                          raw_borrow2, borrow2, fake_seeded_public_key("spot openorders 2"), perp2),
        mango.AccountSlot(2, fake_instrument(), fake_token_info(), fake_token_info(), raw_deposit3, deposit3,
                          raw_borrow3, borrow3, fake_seeded_public_key("spot openorders 3"), perp3),
    ]
    msrm_amount = Decimal(0)
    being_liquidated = False
    is_bankrupt = False

    actual = mango.Account(account_info, mango.Version.V1, meta_data, "Test Group", group, owner, info, quote,
                           in_margin_basket, active_in_basket, basket, msrm_amount, being_liquidated,
                           is_bankrupt)

    assert actual is not None
    assert actual.logger is not None
    assert actual.version == mango.Version.V1
    assert actual.meta_data == meta_data
    assert actual.owner == owner
    assert actual.slot_indices == active_in_basket
    assert actual.in_margin_basket == in_margin_basket
    assert actual.deposits_by_index == [None, deposit1, None, deposit2, deposit3, quote_deposit]
    assert actual.borrows_by_index == [None, borrow1, None, borrow2, borrow3, quote_borrow]
    assert actual.net_values_by_index == [None, deposit1 - borrow1, None,
                                          deposit2 - borrow2, deposit3 - borrow3, quote_deposit - quote_borrow]
    assert actual.spot_open_orders_by_index == [None, fake_seeded_public_key("spot openorders 1"), None, fake_seeded_public_key(
        "spot openorders 2"), fake_seeded_public_key("spot openorders 3"), None]
    assert actual.perp_accounts_by_index == [None, perp1, None, perp2, perp3, None]
    assert actual.msrm_amount == msrm_amount
    assert actual.being_liquidated == being_liquidated
    assert actual.is_bankrupt == is_bankrupt
