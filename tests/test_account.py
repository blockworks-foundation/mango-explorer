import pytest

from .context import mango
from .data import load_data_from_directory
from .fakes import (
    fake_account,
    fake_account_info,
    fake_context,
    fake_seeded_public_key,
    fake_token_bank,
    fake_instrument,
    fake_instrument_value,
    fake_perp_account,
    fake_token,
)

from decimal import Decimal
from mango.layouts import layouts
from solana.publickey import PublicKey


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
    quote = mango.AccountSlot(
        3,
        fake_instrument(),
        fake_token_bank(),
        fake_token_bank(),
        raw_quote_deposit,
        quote_deposit,
        raw_quote_borrow,
        quote_borrow,
        None,
        None,
    )
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
        mango.AccountSlot(
            0,
            fake_instrument(),
            fake_token_bank(),
            fake_token_bank(),
            raw_deposit1,
            deposit1,
            raw_borrow1,
            borrow1,
            fake_seeded_public_key("spot openorders 1"),
            perp1,
        ),
        mango.AccountSlot(
            1,
            fake_instrument(),
            fake_token_bank(),
            fake_token_bank(),
            raw_deposit2,
            deposit2,
            raw_borrow2,
            borrow2,
            fake_seeded_public_key("spot openorders 2"),
            perp2,
        ),
        mango.AccountSlot(
            2,
            fake_instrument(),
            fake_token_bank(),
            fake_token_bank(),
            raw_deposit3,
            deposit3,
            raw_borrow3,
            borrow3,
            fake_seeded_public_key("spot openorders 3"),
            perp3,
        ),
    ]
    msrm_amount = Decimal(0)
    being_liquidated = False
    is_bankrupt = False
    advanced_orders = fake_seeded_public_key("advanced_orders")
    not_upgradable = False
    delegate = fake_seeded_public_key("delegate")

    actual = mango.Account(
        account_info,
        mango.Version.V1,
        meta_data,
        "Test Group",
        group,
        owner,
        info,
        quote,
        in_margin_basket,
        active_in_basket,
        basket,
        msrm_amount,
        being_liquidated,
        is_bankrupt,
        advanced_orders,
        not_upgradable,
        delegate,
    )

    assert actual is not None
    assert actual.version == mango.Version.V1
    assert actual.meta_data == meta_data
    assert actual.owner == owner
    assert actual.slot_indices == active_in_basket
    assert actual.in_margin_basket == in_margin_basket
    assert actual.deposits_by_index == [
        None,
        deposit1,
        None,
        deposit2,
        deposit3,
        quote_deposit,
    ]
    assert actual.borrows_by_index == [
        None,
        borrow1,
        None,
        borrow2,
        borrow3,
        quote_borrow,
    ]
    assert actual.net_values_by_index == [
        None,
        deposit1 - borrow1,
        None,
        deposit2 - borrow2,
        deposit3 - borrow3,
        quote_deposit - quote_borrow,
    ]
    assert actual.spot_open_orders_by_index == [
        None,
        fake_seeded_public_key("spot openorders 1"),
        None,
        fake_seeded_public_key("spot openorders 2"),
        fake_seeded_public_key("spot openorders 3"),
    ]
    assert actual.perp_accounts_by_index == [None, perp1, None, perp2, perp3, None]
    assert actual.msrm_amount == msrm_amount
    assert actual.being_liquidated == being_liquidated
    assert actual.is_bankrupt == is_bankrupt
    assert actual.advanced_orders == advanced_orders
    assert actual.not_upgradable == not_upgradable
    assert actual.delegate == delegate


def test_slot_lookups() -> None:
    account_info = fake_account_info()
    meta_data = mango.Metadata(layouts.DATA_TYPE.Group, mango.Version.V1, True)
    group = fake_seeded_public_key("group")
    owner = fake_seeded_public_key("owner")
    info = "some name"
    in_margin_basket = [False, False, False, False, False, False, False]
    active_in_basket = [False, True, False, True, True, False, False]
    zero_value = Decimal(0)
    quote_slot = mango.AccountSlot(
        3,
        fake_token("FAKEQUOTE"),
        fake_token_bank("FAKEQUOTE"),
        fake_token_bank(),
        zero_value,
        fake_instrument_value(Decimal(10)),
        zero_value,
        fake_instrument_value(Decimal(2)),
        None,
        None,
    )
    perp2 = fake_perp_account()
    perp3 = fake_perp_account()
    slots = [
        mango.AccountSlot(
            1,
            fake_instrument("slot1"),
            fake_token_bank(),
            fake_token_bank(),
            zero_value,
            fake_instrument_value(Decimal(2)),
            zero_value,
            fake_instrument_value(Decimal(1)),
            fake_seeded_public_key("spot openorders 1"),
            None,
        ),
        mango.AccountSlot(
            3,
            fake_token("MNGO"),
            fake_token_bank("MNGO"),
            fake_token_bank(),
            zero_value,
            fake_instrument_value(Decimal(6)),
            zero_value,
            fake_instrument_value(Decimal(4)),
            fake_seeded_public_key("spot openorders 2"),
            perp2,
        ),
        mango.AccountSlot(
            4,
            fake_instrument("slot3"),
            fake_token_bank(),
            fake_token_bank(),
            zero_value,
            fake_instrument_value(Decimal(5)),
            zero_value,
            fake_instrument_value(Decimal(8)),
            None,
            perp3,
        ),
    ]
    msrm_amount = Decimal(0)
    being_liquidated = False
    is_bankrupt = False
    advanced_orders = fake_seeded_public_key("advanced_orders")
    not_upgradable = False
    delegate = fake_seeded_public_key("delegate")

    actual = mango.Account(
        account_info,
        mango.Version.V1,
        meta_data,
        "Test Group",
        group,
        owner,
        info,
        quote_slot,
        in_margin_basket,
        active_in_basket,
        slots,
        msrm_amount,
        being_liquidated,
        is_bankrupt,
        advanced_orders,
        not_upgradable,
        delegate,
    )

    assert actual.shared_quote == quote_slot
    assert actual.shared_quote_token == quote_slot.base_instrument

    assert len(actual.base_slots) == 3  # Shared Quote is NOT included
    assert actual.base_slots[0] == slots[0]
    assert actual.base_slots[1] == slots[1]
    assert actual.base_slots[2] == slots[2]

    assert len(actual.slots) == 4  # Shared Quote is included
    assert actual.slots[0] == slots[0]
    assert actual.slots[1] == slots[1]
    assert actual.slots[2] == slots[2]
    assert actual.slots[3] == quote_slot

    assert len(actual.slots_by_index) == 8  # Shared Quote is included
    assert actual.slots_by_index[0] is None
    assert actual.slots_by_index[1] == slots[0]
    assert actual.slots_by_index[2] is None
    assert actual.slots_by_index[3] == slots[1]
    assert actual.slots_by_index[4] == slots[2]
    assert actual.slots_by_index[5] is None
    assert actual.slots_by_index[6] is None
    assert actual.slots_by_index[7] == quote_slot

    assert len(actual.deposits) == 4  # Shared Quote is included
    assert actual.deposits[0] == slots[0].deposit
    assert actual.deposits[1] == slots[1].deposit
    assert actual.deposits[2] == slots[2].deposit
    assert actual.deposits[3] == quote_slot.deposit

    assert len(actual.deposits_by_index) == 8  # Shared Quote is included
    assert actual.deposits_by_index[0] is None
    assert actual.deposits_by_index[1] == slots[0].deposit
    assert actual.deposits_by_index[2] is None
    assert actual.deposits_by_index[3] == slots[1].deposit
    assert actual.deposits_by_index[4] == slots[2].deposit
    assert actual.deposits_by_index[5] is None
    assert actual.deposits_by_index[6] is None
    assert actual.deposits_by_index[7] == quote_slot.deposit

    assert len(actual.borrows) == 4  # Shared Quote is included
    assert actual.borrows[0] == slots[0].borrow
    assert actual.borrows[1] == slots[1].borrow
    assert actual.borrows[2] == slots[2].borrow
    assert actual.borrows[3] == quote_slot.borrow

    assert len(actual.borrows_by_index) == 8  # Shared Quote is included
    assert actual.borrows_by_index[0] is None
    assert actual.borrows_by_index[1] == slots[0].borrow
    assert actual.borrows_by_index[2] is None
    assert actual.borrows_by_index[3] == slots[1].borrow
    assert actual.borrows_by_index[4] == slots[2].borrow
    assert actual.borrows_by_index[5] is None
    assert actual.borrows_by_index[6] is None
    assert actual.borrows_by_index[7] == quote_slot.borrow

    assert len(actual.net_values) == 4  # Shared Quote is included
    assert actual.net_values[0] == slots[0].net_value
    assert actual.net_values[1] == slots[1].net_value
    assert actual.net_values[2] == slots[2].net_value
    assert actual.net_values[3] == quote_slot.net_value

    assert len(actual.net_values_by_index) == 8  # Shared Quote is included
    assert actual.net_values_by_index[0] is None
    assert actual.net_values_by_index[1] == slots[0].net_value
    assert actual.net_values_by_index[2] is None
    assert actual.net_values_by_index[3] == slots[1].net_value
    assert actual.net_values_by_index[4] == slots[2].net_value
    assert actual.net_values_by_index[5] is None
    assert actual.net_values_by_index[6] is None
    assert actual.net_values_by_index[7] == quote_slot.net_value

    # Shared Quote should always have None for spot_open_orders so is not included
    assert len(actual.spot_open_orders) == 2
    assert actual.spot_open_orders[0] == slots[0].spot_open_orders
    assert actual.spot_open_orders[1] == slots[1].spot_open_orders

    assert (
        len(actual.spot_open_orders_by_index) == 7
    )  # Shared Quote is included but should always be None
    assert actual.spot_open_orders_by_index[0] is None
    assert actual.spot_open_orders_by_index[1] == slots[0].spot_open_orders
    assert actual.spot_open_orders_by_index[2] is None
    assert actual.spot_open_orders_by_index[3] == slots[1].spot_open_orders
    assert actual.spot_open_orders_by_index[4] is None
    assert actual.spot_open_orders_by_index[5] is None
    assert actual.spot_open_orders_by_index[6] is None

    # Shared Quote should always have None for perp_account so is not included
    assert len(actual.perp_accounts) == 2
    assert actual.perp_accounts[0] == slots[1].perp_account
    assert actual.perp_accounts[1] == slots[2].perp_account

    assert (
        len(actual.perp_accounts_by_index) == 8
    )  # Shared Quote is included but should always be None
    assert actual.perp_accounts_by_index[0] is None
    assert actual.perp_accounts_by_index[1] is None
    assert actual.perp_accounts_by_index[2] is None
    assert actual.perp_accounts_by_index[3] == slots[1].perp_account
    assert actual.perp_accounts_by_index[4] == slots[2].perp_account
    assert actual.perp_accounts_by_index[5] is None
    assert actual.perp_accounts_by_index[6] is None
    assert actual.perp_accounts_by_index[7] is None

    assert actual.slot_by_instrument_or_none(fake_instrument()) is None
    assert actual.slot_by_instrument_or_none(fake_token("MNGO")) == slots[1]
    assert actual.slot_by_instrument_or_none(fake_instrument("slot3")) == slots[2]
    assert actual.slot_by_instrument_or_none(fake_token("FAKEQUOTE")) == quote_slot

    assert actual.slot_by_instrument(fake_instrument("slot3")) == slots[2]
    with pytest.raises(Exception):
        assert actual.slot_by_instrument(fake_instrument())


def test_loaded_account_slot_lookups() -> None:
    group, cache, account, open_orders = load_data_from_directory(
        "tests/testdata/account5"
    )
    assert len(account.slots) == 14

    # « GroupSlot[0] « Token [MNGO] 'MNGO' [Bb9bsTQa1bGEtQ5KagGkvSHyuLqDWumFUcRqFusFNJWC (6 decimals)] »
    assert account.slots_by_index[0] is not None
    assert account.slots_by_index[0].base_instrument.symbol == "MNGO"

    # « GroupSlot[1] « Token [BTC] 'BTC' [3UNBZ6o52WTWwjac2kPUb4FyodhU1vFkRJheu1Sh2TvU (6 decimals)] »
    assert account.slots_by_index[1] is not None
    assert account.slots_by_index[1].base_instrument.symbol == "BTC"

    # « GroupSlot[2] « Token [ETH] 'ETH' [Cu84KB3tDL6SbFgToHMLYVDJJXdJjenNzSKikeAvzmkA (6 decimals)] »
    assert account.slots_by_index[2] is not None
    assert account.slots_by_index[2].base_instrument.symbol == "ETH"

    # « GroupSlot[3] « Token [SOL] 'SOL' [So11111111111111111111111111111111111111112 (9 decimals)] »
    assert account.slots_by_index[3] is not None
    assert account.slots_by_index[3].base_instrument.symbol == "SOL"

    # « GroupSlot[4] « Token [SRM] 'SRM' [AvtB6w9xboLwA145E221vhof5TddhqsChYcx7Fy3xVMH (6 decimals)] »
    assert account.slots_by_index[4] is not None
    assert account.slots_by_index[4].base_instrument.symbol == "SRM"

    # « GroupSlot[5] « Token [RAY] 'RAY' [3YFQ7UYJ7sNGpXTKBxM3bYLVxKpzVudXAe4gLExh5b3n (6 decimals)] »
    assert account.slots_by_index[5] is not None
    assert account.slots_by_index[5].base_instrument.symbol == "RAY"

    # « GroupSlot[6] « Token [USDT] 'USDT' [DAwBSXe6w9g37wdE2tCrFbho3QHKZi4PjuBytQCULap2 (6 decimals)] »
    assert account.slots_by_index[6] is not None
    assert account.slots_by_index[6].base_instrument.symbol == "USDT"

    # « GroupSlot[7] « Instrument [ADA] 'Cardano' »
    assert account.slots_by_index[7] is not None
    assert account.slots_by_index[7].base_instrument.symbol == "ADA"

    # « GroupSlot[8] « Token [FTT] 'FTT' [Fxh4bpZnRCnpg2vcH11ttmSTDSEeC5qWbPRZNZWnRnqY (6 decimals)] »
    assert account.slots_by_index[8] is not None
    assert account.slots_by_index[8].base_instrument.symbol == "FTT"

    # « GroupSlot[9] « Instrument [AVAX] 'Avalanche' »
    assert account.slots_by_index[9] is not None
    assert account.slots_by_index[9].base_instrument.symbol == "AVAX"

    # « GroupSlot[10] « Instrument [LUNA] 'Terra' »
    assert account.slots_by_index[10] is not None
    assert account.slots_by_index[10].base_instrument.symbol == "LUNA"

    # « GroupSlot[11] « Instrument [BNB] 'Binance Coin' »
    assert account.slots_by_index[11] is not None
    assert account.slots_by_index[11].base_instrument.symbol == "BNB"

    # « GroupSlot[12] « Instrument [MATIC] 'Polygon' »
    assert account.slots_by_index[12] is not None
    assert account.slots_by_index[12].base_instrument.symbol == "MATIC"
    assert account.slots_by_index[13] is None
    assert account.slots_by_index[14] is None
    assert account.slots_by_index[15] is not None
    assert account.slots_by_index[15].base_instrument.symbol == "USDC"


def test_derive_referrer_memory_address() -> None:
    context = fake_context(
        mango_program_address=PublicKey("4skJ85cdxQAFVKbcGgfun8iZPL7BadVYXG3kGEGkufqA")
    )
    account = fake_account(
        address=PublicKey("FG99s25HS1UKcP1jMx72Gezg6KZCC7DuKXhNW51XC1qi")
    )
    actual = account.derive_referrer_memory_address(context)

    # Value derived using mango-client-v3: 3CMpC1UzdLrAnGz6HZVoBsDLAHpTABkUJr8iPyEHwehr
    expected = PublicKey("3CMpC1UzdLrAnGz6HZVoBsDLAHpTABkUJr8iPyEHwehr")

    assert actual == expected
