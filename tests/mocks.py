from .context import mango
from .fakes import fake_account_info, fake_context, fake_seeded_public_key

import typing

from decimal import Decimal
from mango.layouts import layouts

#
# Mocks are more involved than fakes, but do tend to allow more introspection.
#

token_lookup = fake_context().token_lookup
ETH = token_lookup.find_by_symbol_or_raise("ETH")
BTC = token_lookup.find_by_symbol_or_raise("BTC")
SOL = token_lookup.find_by_symbol_or_raise("SOL")
SRM = token_lookup.find_by_symbol_or_raise("SRM")
USDC = token_lookup.find_by_symbol_or_raise("USDC")


def mock_group():
    account_info = fake_account_info()
    name = "FAKE_GROUP"
    meta_data = mango.Metadata(layouts.DATA_TYPE.Group, mango.Version.V1, True)
    btc_info = mango.TokenInfo(BTC, fake_seeded_public_key("root bank"), Decimal(6))
    usdc_info = mango.TokenInfo(USDC, fake_seeded_public_key("root bank"), Decimal(6))
    token_infos = [btc_info, None, usdc_info]
    spot_markets = []
    perp_markets = []
    oracles = []
    signer_nonce = Decimal(1)
    signer_key = fake_seeded_public_key("signer key")
    admin_key = fake_seeded_public_key("admin key")
    serum_program_address = fake_seeded_public_key("DEX program ID")
    cache_key = fake_seeded_public_key("cache key")
    valid_interval = Decimal(7)

    return mango.Group(account_info, mango.Version.V1, name, meta_data, token_infos,
                       spot_markets, perp_markets, oracles, signer_nonce, signer_key,
                       admin_key, serum_program_address, cache_key, valid_interval)


def mock_prices(prices: typing.Sequence[str]):
    eth, btc, sol, srm, usdc = prices
    return [
        mango.TokenValue(ETH, Decimal(eth)),
        mango.TokenValue(BTC, Decimal(btc)),
        mango.TokenValue(SOL, Decimal(sol)),
        mango.TokenValue(SRM, Decimal(srm)),
        mango.TokenValue(USDC, Decimal(usdc)),
    ]


def mock_open_orders(base_token_free: Decimal = Decimal(0), base_token_total: Decimal = Decimal(0), quote_token_free: Decimal = Decimal(0), quote_token_total: Decimal = Decimal(0), referrer_rebate_accrued: Decimal = Decimal(0)):
    account_info = fake_account_info()
    program_address = fake_seeded_public_key("program address")
    market = fake_seeded_public_key("market")
    owner = fake_seeded_public_key("owner")

    flags = mango.AccountFlags(mango.Version.V1, True, False, True, False, False, False, False, False)
    return mango.OpenOrders(account_info, mango.Version.V1, program_address, flags, market,
                            owner, base_token_free, base_token_total, quote_token_free,
                            quote_token_total, [], referrer_rebate_accrued)
