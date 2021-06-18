from .context import mango

from decimal import Decimal
from solana.publickey import PublicKey


def test_token_constructor():
    symbol = "TEST"
    name = "Test Token"
    mint = PublicKey("11111111111111111111111111111113")
    decimals = Decimal(18)
    actual = mango.Token(symbol, name, mint, decimals)
    assert actual is not None
    assert actual.logger is not None
    assert actual.symbol == symbol
    assert actual.name == name
    assert actual.mint == mint
    assert actual.decimals == decimals


def test_token_lookup():
    data = {
        "tokens": [
            {
                "address": "So11111111111111111111111111111111111111112",
                "symbol": "SOL",
                "name": "Wrapped SOL",
                "decimals": 9,
            },
            {
                "address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                "symbol": "USDC",
                "name": "USD Coin",
                "decimals": 6,
            },
            {
                "address": "9n4nbM75f5Ui33ZbPYXn59EwSgE8CGsHtAeTH5YFeJ9E",
                "symbol": "BTC",
                "name": "Wrapped Bitcoin (Sollet)",
                "decimals": 6,
            },
            {
                "address": "2FPyTwcZLUg1MDrwsyoP4D6s1tM7hAkHYRjkNb5w6Pxk",
                "symbol": "ETH",
                "name": "Wrapped Ethereum (Sollet)",
                "decimals": 6,
            }]
    }
    actual = mango.TokenLookup(data)
    assert actual is not None
    assert actual.logger is not None
    assert actual.find_by_symbol("ETH") is not None
    assert actual.find_by_symbol("ETH").name == "Wrapped Ethereum (Sollet)"
    assert actual.find_by_symbol("BTC") is not None
    assert actual.find_by_symbol("BTC").name == "Wrapped Bitcoin (Sollet)"


def test_token_lookups_with_full_data():
    token_lookup = mango.TokenLookup.load(mango.TokenLookup.DEFAULT_FILE_NAME)
    assert token_lookup.find_by_symbol("BTC").mint == PublicKey("9n4nbM75f5Ui33ZbPYXn59EwSgE8CGsHtAeTH5YFeJ9E")
    assert token_lookup.find_by_symbol("ETH").mint == PublicKey("2FPyTwcZLUg1MDrwsyoP4D6s1tM7hAkHYRjkNb5w6Pxk")
    assert token_lookup.find_by_mint("AKJHspCwDhABucCxNLXUSfEzb7Ny62RqFtC9uNjJi4fq").symbol == "SRM-SOL"
    assert token_lookup.find_by_mint("Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB").symbol == "USDT"
