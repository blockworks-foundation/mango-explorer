import pytest
import typing

from .context import mango
from .fakes import fake_account_info, fake_seeded_public_key, fake_token_bank, fake_instrument

from decimal import Decimal
from mango.layouts import layouts


def test_construction() -> None:
    account_info = fake_account_info()
    name = "FAKE_GROUP"
    meta_data = mango.Metadata(layouts.DATA_TYPE.Group, mango.Version.V1, True)
    shared_quote_token = fake_token_bank()
    in_basket: typing.Sequence[bool] = []
    slots: typing.Sequence[mango.GroupSlot] = []
    signer_nonce = Decimal(1)
    signer_key = fake_seeded_public_key("signer key")
    admin_key = fake_seeded_public_key("admin key")
    serum_program_address = fake_seeded_public_key("Serum program ID")
    cache_key = fake_seeded_public_key("cache key")
    valid_interval = Decimal(7)
    insurance_vault = fake_seeded_public_key("insurance vault")
    srm_vault = fake_seeded_public_key("SRM vault")
    msrm_vault = fake_seeded_public_key("MSRM vault")
    fees_vault = fake_seeded_public_key("fees vault")

    actual = mango.Group(account_info, mango.Version.V1, name, meta_data, shared_quote_token, in_basket,
                         slots, signer_nonce, signer_key, admin_key, serum_program_address,
                         cache_key, valid_interval, insurance_vault, srm_vault, msrm_vault, fees_vault)

    assert actual is not None
    assert actual.logger is not None
    assert actual.name == name
    assert actual.meta_data == meta_data
    assert actual.shared_quote_token == shared_quote_token.token
    assert actual.shared_quote == shared_quote_token
    assert actual.slot_indices == in_basket
    assert actual.slots == slots
    assert actual.signer_nonce == signer_nonce
    assert actual.signer_key == signer_key
    assert actual.admin == admin_key
    assert actual.serum_program_address == serum_program_address
    assert actual.cache == cache_key
    assert actual.valid_interval == valid_interval
    assert actual.insurance_vault == insurance_vault
    assert actual.srm_vault == srm_vault
    assert actual.msrm_vault == msrm_vault
    assert actual.fees_vault == fees_vault


def test_slot_lookups() -> None:
    # This bit is mostly prologue.
    account_info = fake_account_info()
    name = "FAKE_GROUP"
    meta_data = mango.Metadata(layouts.DATA_TYPE.Group, mango.Version.V1, True)
    signer_nonce = Decimal(1)
    signer_key = fake_seeded_public_key("signer key")
    admin_key = fake_seeded_public_key("admin key")
    serum_program_address = fake_seeded_public_key("Serum program ID")
    cache_key = fake_seeded_public_key("cache key")
    valid_interval = Decimal(7)
    insurance_vault = fake_seeded_public_key("insurance vault")
    srm_vault = fake_seeded_public_key("SRM vault")
    msrm_vault = fake_seeded_public_key("MSRM vault")
    fees_vault = fake_seeded_public_key("fees vault")

    # This is the more relevant stuff here.
    shared_quote_token_bank = fake_token_bank("FAKEQUOTE")
    slot1_token_bank = fake_token_bank("slot1")
    mngo_token_bank = fake_token_bank("MNGO")
    slot3_instrument = fake_instrument("slot3")
    in_basket: typing.Sequence[bool] = [False, True, False, False, True, False, True, False]
    spot_market1 = mango.GroupSlotSpotMarket(fake_seeded_public_key("spot market 1"),
                                             Decimal(0), Decimal(0), Decimal(0), Decimal(0))
    spot_market2 = mango.GroupSlotSpotMarket(fake_seeded_public_key("spot market 2"),
                                             Decimal(0), Decimal(0), Decimal(0), Decimal(0))
    perp_market2 = mango.GroupSlotPerpMarket(fake_seeded_public_key("perp market 2"), Decimal(0), Decimal(0),
                                             Decimal(0), Decimal(0), Decimal(0), Decimal(0), Decimal(0))
    perp_market3 = mango.GroupSlotPerpMarket(fake_seeded_public_key("perp market 3"), Decimal(0), Decimal(0),
                                             Decimal(0), Decimal(0), Decimal(0), Decimal(0), Decimal(0))
    slot1 = mango.GroupSlot(1, slot1_token_bank.token, slot1_token_bank, shared_quote_token_bank, spot_market1,
                            None, mango.NullLotSizeConverter(), fake_seeded_public_key("oracle 1"))
    # MNGO is a special case since that's the current name used for liquidity tokens.
    slot2 = mango.GroupSlot(4, mngo_token_bank.token, mngo_token_bank, shared_quote_token_bank, spot_market2,
                            perp_market2, mango.NullLotSizeConverter(), fake_seeded_public_key("oracle 2"))
    slot3 = mango.GroupSlot(6, slot3_instrument, None, shared_quote_token_bank, None, perp_market3,
                            mango.NullLotSizeConverter(), fake_seeded_public_key("oracle 3"))
    slots: typing.Sequence[mango.GroupSlot] = [slot1, slot2, slot3]

    actual = mango.Group(account_info, mango.Version.V1, name, meta_data, shared_quote_token_bank, in_basket,
                         slots, signer_nonce, signer_key, admin_key, serum_program_address,
                         cache_key, valid_interval, insurance_vault, srm_vault, msrm_vault, fees_vault)

    assert actual.shared_quote == shared_quote_token_bank
    assert actual.liquidity_incentive_token_bank == mngo_token_bank
    assert actual.liquidity_incentive_token == mngo_token_bank.token

    assert len(actual.tokens) == 3  # Shared Quote is included, slot3 has no TokenBank so is not a Token
    assert actual.tokens[0] == slot1.base_token_bank
    assert actual.tokens[1] == slot2.base_token_bank
    assert actual.tokens[2] == shared_quote_token_bank

    assert len(actual.tokens_by_index) == 9  # Shared Quote is included
    assert actual.tokens_by_index[0] is None
    assert actual.tokens_by_index[1] == slot1.base_token_bank
    assert actual.tokens_by_index[2] is None
    assert actual.tokens_by_index[3] is None
    assert actual.tokens_by_index[4] == slot2.base_token_bank
    assert actual.tokens_by_index[5] is None
    assert actual.tokens_by_index[6] is None
    assert actual.tokens_by_index[7] is None
    assert actual.tokens_by_index[8] == shared_quote_token_bank

    assert len(actual.slots) == 3  # Shared Quote is NOT included
    assert actual.slots[0] == slot1
    assert actual.slots[1] == slot2
    assert actual.slots[2] == slot3

    assert len(actual.slots_by_index) == 8  # Shared Quote is NOT included
    assert actual.slots_by_index[0] is None
    assert actual.slots_by_index[1] == slot1
    assert actual.slots_by_index[2] is None
    assert actual.slots_by_index[3] is None
    assert actual.slots_by_index[4] == slot2
    assert actual.slots_by_index[5] is None
    assert actual.slots_by_index[6] == slot3
    assert actual.slots_by_index[7] is None

    assert len(actual.base_tokens) == 2  # slot3 has no TokenBank so is not a Token
    assert actual.base_tokens[0] == slot1.base_token_bank
    assert actual.base_tokens[1] == slot2.base_token_bank

    assert len(actual.base_tokens_by_index) == 8  # Shared Quote is NOT included
    assert actual.base_tokens_by_index[0] is None
    assert actual.base_tokens_by_index[1] == slot1.base_token_bank
    assert actual.base_tokens_by_index[2] is None
    assert actual.base_tokens_by_index[3] is None
    assert actual.base_tokens_by_index[4] == slot2.base_token_bank
    assert actual.base_tokens_by_index[5] is None
    assert actual.base_tokens_by_index[6] is None
    assert actual.base_tokens_by_index[7] is None

    assert len(actual.oracles) == 3  # Shared Quote is NOT included
    assert actual.oracles[0] == slot1.oracle
    assert actual.oracles[1] == slot2.oracle
    assert actual.oracles[2] == slot3.oracle

    assert len(actual.oracles_by_index) == 8  # Shared Quote is NOT included
    assert actual.oracles_by_index[0] is None
    assert actual.oracles_by_index[1] == slot1.oracle
    assert actual.oracles_by_index[2] is None
    assert actual.oracles_by_index[3] is None
    assert actual.oracles_by_index[4] == slot2.oracle
    assert actual.oracles_by_index[5] is None
    assert actual.oracles_by_index[6] == slot3.oracle
    assert actual.oracles_by_index[7] is None

    assert len(actual.spot_markets) == 2  # Shared Quote is NOT included
    assert actual.spot_markets[0] == slot1.spot_market
    assert actual.spot_markets[1] == slot2.spot_market

    assert len(actual.spot_markets_by_index) == 8  # Shared Quote is NOT included
    assert actual.spot_markets_by_index[0] is None
    assert actual.spot_markets_by_index[1] == slot1.spot_market
    assert actual.spot_markets_by_index[2] is None
    assert actual.spot_markets_by_index[3] is None
    assert actual.spot_markets_by_index[4] == slot2.spot_market
    assert actual.spot_markets_by_index[5] is None
    assert actual.spot_markets_by_index[6] is None
    assert actual.spot_markets_by_index[7] is None

    assert len(actual.perp_markets) == 2  # Shared Quote is NOT included
    assert actual.perp_markets[0] == slot2.perp_market
    assert actual.perp_markets[1] == slot3.perp_market

    assert len(actual.perp_markets_by_index) == 8  # Shared Quote is NOT included
    assert actual.perp_markets_by_index[0] is None
    assert actual.perp_markets_by_index[1] is None
    assert actual.perp_markets_by_index[2] is None
    assert actual.perp_markets_by_index[3] is None
    assert actual.perp_markets_by_index[4] == slot2.perp_market
    assert actual.perp_markets_by_index[5] is None
    assert actual.perp_markets_by_index[6] == slot3.perp_market
    assert actual.perp_markets_by_index[7] is None

    assert actual.slot_by_spot_market_address(fake_seeded_public_key("spot market 1")) == slot1
    assert actual.slot_by_spot_market_address(fake_seeded_public_key("spot market 2")) == slot2

    assert actual.slot_by_perp_market_address(fake_seeded_public_key("perp market 2")) == slot2
    assert actual.slot_by_perp_market_address(fake_seeded_public_key("perp market 3")) == slot3

    assert actual.slot_by_instrument_or_none(fake_instrument()) is None
    assert actual.slot_by_instrument_or_none(fake_instrument("slot3")) == slot3
    assert actual.slot_by_instrument(fake_instrument("slot3")) == slot3
    with pytest.raises(Exception):
        assert actual.slot_by_instrument(fake_instrument())
