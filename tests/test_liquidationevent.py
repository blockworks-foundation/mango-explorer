from .context import mango
from .fakes import fake_public_key

from decimal import Decimal

import datetime


def test_liquidation_event():
    token_lookup = mango.TokenLookup.default_lookups()
    balances_before = [
        mango.TokenValue(token_lookup.find_by_symbol("ETH"), Decimal(1)),
        mango.TokenValue(token_lookup.find_by_symbol("BTC"), Decimal("0.1")),
        mango.TokenValue(token_lookup.find_by_symbol("USDT"), Decimal(1000))
    ]
    balances_after = [
        mango.TokenValue(token_lookup.find_by_symbol("ETH"), Decimal(1)),
        mango.TokenValue(token_lookup.find_by_symbol("BTC"), Decimal("0.05")),
        mango.TokenValue(token_lookup.find_by_symbol("USDT"), Decimal(2000))
    ]
    timestamp = datetime.datetime(2021, 5, 17, 12, 20, 56)
    event = mango.LiquidationEvent(timestamp, "Liquidator", "Group", True, "signature",
                                   fake_public_key(), fake_public_key(),
                                   balances_before, balances_after)
    assert str(event) == """« 🥭 Liqudation Event ✅ at 2021-05-17 12:20:56
    💧 Liquidator: Liquidator
    🗃️ Group: Group
    📇 Signature: signature
    👛 Wallet: 11111111111111111111111111111112
    💳 Margin Account: 11111111111111111111111111111112
    💸 Changes:
             0.00000000 ETH
            -0.05000000 BTC
         1,000.00000000 USDT
»"""
