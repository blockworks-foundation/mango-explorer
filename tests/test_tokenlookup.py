from .context import mango

from solana.publickey import PublicKey


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
    actual = mango.SplTokenLookup("test-filename", data)
    assert actual is not None
    assert actual.logger is not None
    assert actual.find_by_symbol("ETH") is not None
    assert actual.find_by_symbol("ETH").name == "Wrapped Ethereum (Sollet)"
    assert actual.find_by_symbol("BTC") is not None
    assert actual.find_by_symbol("BTC").name == "Wrapped Bitcoin (Sollet)"


def test_token_lookups_with_full_data():
    token_lookup = mango.SplTokenLookup.load(mango.SplTokenLookup.DefaultDataFilepath)
    assert token_lookup.find_by_symbol("BTC").mint == PublicKey("9n4nbM75f5Ui33ZbPYXn59EwSgE8CGsHtAeTH5YFeJ9E")
    assert token_lookup.find_by_symbol("ETH").mint == PublicKey("2FPyTwcZLUg1MDrwsyoP4D6s1tM7hAkHYRjkNb5w6Pxk")
    assert token_lookup.find_by_mint("AKJHspCwDhABucCxNLXUSfEzb7Ny62RqFtC9uNjJi4fq").symbol == "SRM-SOL"
    assert token_lookup.find_by_mint("Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB").symbol == "USDT"
