from .context import mango
from .fakes import fake_account_info, fake_context, fake_seeded_public_key

import typing

from datetime import datetime
from decimal import Decimal
from solana.publickey import PublicKey

#
# Mocks are more involved than fakes, but do tend to allow more introspection.
#

token_lookup = fake_context().token_lookup
ETH = token_lookup.find_by_symbol("ETH")
BTC = token_lookup.find_by_symbol("BTC")
SOL = token_lookup.find_by_symbol("SOL")
SRM = token_lookup.find_by_symbol("SRM")
USDC = token_lookup.find_by_symbol("USDC")


def mock_group():
    account_info = fake_account_info()
    name = "FAKE_GROUP"
    account_flags = mango.MangoAccountFlags(mango.Version.V1, True, False, True, False)

    def index(token):
        borrow = mango.TokenValue(token, Decimal(1))
        deposit = mango.TokenValue(token, Decimal(1))
        return mango.Index(mango.Version.V1, token, datetime.now(), borrow, deposit)

    basket_tokens = [
        mango.BasketToken(ETH, fake_seeded_public_key("ETH vault"), index(ETH)),
        mango.BasketToken(BTC, fake_seeded_public_key("BTC vault"), index(ETH)),
        mango.BasketToken(SOL, fake_seeded_public_key("SOL vault"), index(ETH)),
        mango.BasketToken(SRM, fake_seeded_public_key("SRM vault"), index(ETH)),
        mango.BasketToken(USDC, fake_seeded_public_key("USDC vault"), index(ETH))
    ]

    markets = []
    signer_nonce = Decimal(1)
    signer_key = fake_seeded_public_key("signer key")
    dex_program_id = fake_seeded_public_key("DEX program ID")
    total_deposits = [
        mango.TokenValue(ETH, Decimal(1000)),
        mango.TokenValue(BTC, Decimal(1000)),
        mango.TokenValue(SOL, Decimal(1000)),
        mango.TokenValue(SRM, Decimal(1000)),
        mango.TokenValue(USDC, Decimal(1000)),
    ]
    total_borrows = [
        mango.TokenValue(ETH, Decimal(0)),
        mango.TokenValue(BTC, Decimal(0)),
        mango.TokenValue(SOL, Decimal(0)),
        mango.TokenValue(SRM, Decimal(0)),
        mango.TokenValue(USDC, Decimal(0)),
    ]
    maint_coll_ratio = Decimal("1.1")
    init_coll_ratio = Decimal("1.2")
    srm_vault = fake_seeded_public_key("SRM vault")
    admin = fake_seeded_public_key("admin")
    borrow_limits = [Decimal(10), Decimal(10), Decimal(10), Decimal(10), Decimal(10)]

    return mango.Group(account_info, mango.Version.V1, name, account_flags,
                       basket_tokens, markets, signer_nonce, signer_key, dex_program_id,
                       total_deposits, total_borrows, maint_coll_ratio, init_coll_ratio,
                       srm_vault, admin, borrow_limits)


def mock_prices(prices: typing.List[str]):
    eth, btc, sol, srm, usdc = prices
    return [
        mango.TokenValue(ETH, Decimal(eth)),
        mango.TokenValue(BTC, Decimal(btc)),
        mango.TokenValue(SOL, Decimal(sol)),
        mango.TokenValue(SRM, Decimal(srm)),
        mango.TokenValue(USDC, Decimal(usdc)),
    ]


def mock_margin_account(group: mango.Group, deposits: typing.List[str], borrows: typing.List[str], openorders: typing.List[typing.Optional[mango.OpenOrders]]):
    eth, btc, sol, srm, usdc = deposits
    token_deposits = [
        mango.TokenValue(ETH, Decimal(eth)),
        mango.TokenValue(BTC, Decimal(btc)),
        mango.TokenValue(SOL, Decimal(sol)),
        mango.TokenValue(SRM, Decimal(srm)),
        mango.TokenValue(USDC, Decimal(usdc)),
    ]
    eth, btc, sol, srm, usdc = borrows
    token_borrows = [
        mango.TokenValue(ETH, Decimal(eth)),
        mango.TokenValue(BTC, Decimal(btc)),
        mango.TokenValue(SOL, Decimal(sol)),
        mango.TokenValue(SRM, Decimal(srm)),
        mango.TokenValue(USDC, Decimal(usdc)),
    ]

    account_flags = mango.MangoAccountFlags(mango.Version.V1, True, False, True, False)
    has_borrows = False
    owner = fake_seeded_public_key("owner")
    open_orders_keys: typing.List[typing.Optional[PublicKey]] = []
    for oo in openorders:
        if oo is None:
            open_orders_keys += [None]
        else:
            open_orders_keys += [oo.address]
    margin_account = mango.MarginAccount(fake_account_info(), mango.Version.V1, account_flags,
                                         has_borrows, group.address, owner, token_deposits, token_borrows,
                                         open_orders_keys)
    margin_account.open_orders_accounts = openorders
    return margin_account


def mock_open_orders(base_token_free: Decimal = Decimal(0), base_token_total: Decimal = Decimal(0), quote_token_free: Decimal = Decimal(0), quote_token_total: Decimal = Decimal(0), referrer_rebate_accrued: Decimal = Decimal(0)):
    account_info = fake_account_info()
    program_id = fake_seeded_public_key("program ID")
    market = fake_seeded_public_key("market")
    owner = fake_seeded_public_key("owner")

    flags = mango.SerumAccountFlags(mango.Version.V1, True, False, True, False, False, False, False, False)
    return mango.OpenOrders(account_info, mango.Version.V1, program_id, flags, market,
                            owner, base_token_free, base_token_total, quote_token_free,
                            quote_token_total, Decimal(0), Decimal(0), [], [],
                            referrer_rebate_accrued)
