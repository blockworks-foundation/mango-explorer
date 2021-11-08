from .context import mango
from .fakes import fake_account_info, fake_seeded_public_key, fake_token_info

from decimal import Decimal
from mango.layouts import layouts


def test_construction():
    account_info = fake_account_info()
    name = "FAKE_GROUP"
    meta_data = mango.Metadata(layouts.DATA_TYPE.Group, mango.Version.V1, True)
    shared_quote_token = fake_token_info()
    in_basket = []
    slots = []
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
