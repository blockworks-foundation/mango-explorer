from .context import mango, disable_logging

from solana.publickey import PublicKey

from .fakes import fake_seeded_public_key


def test_market_symbol_matching() -> None:
    assert mango.Market.symbols_match("BTC/USDC", "BTC/USDC")
    assert mango.Market.symbols_match("eth/usdc", "eth/usdc")
    assert mango.Market.symbols_match("btc/usdc", "BTC/USDC")
    assert mango.Market.symbols_match("ETH/USDC", "eth/usdc")
    assert mango.Market.symbols_match("serum:ETH/USDC", "serum:eth/usdc")
    assert not mango.Market.symbols_match("ETH/USDC", "BTC/USDC")
    assert not mango.Market.symbols_match("serum:ETH/USDC", "spot:eth/usdc")


def test_serum_market_lookup() -> None:
    data = {
        "tokens": [
            {
                "chainId": 101,
                "address": "So11111111111111111111111111111111111111112",
                "symbol": "SOL",
                "name": "Wrapped SOL",
                "decimals": 9,
                "logoURI": "https://cdn.jsdelivr.net/gh/trustwallet/assets@master/blockchains/solana/info/logo.png",
                "tags": [],
                "extensions": {
                    "website": "https://solana.com/",
                    "serumV3Usdc": "9wFFyRfZBsuAha4YcuxcXLKwMxJR43S7fPfQLusDBzvT",
                    "serumV3Usdt": "HWHvQhFmJB3NUcu1aihKmrKegfVxBEHzwVX6yZCKEsi1",
                    "coingeckoId": "solana",
                },
            },
            {
                "chainId": 101,
                "address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                "symbol": "USDC",
                "name": "USD Coin",
                "decimals": 6,
                "logoURI": "https://cdn.jsdelivr.net/gh/solana-labs/token-list@main/assets/mainnet/EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v/logo.png",
                "tags": ["stablecoin"],
                "extensions": {
                    "website": "https://www.centre.io/",
                    "coingeckoId": "usd-coin",
                },
            },
            {
                "chainId": 101,
                "address": "9n4nbM75f5Ui33ZbPYXn59EwSgE8CGsHtAeTH5YFeJ9E",
                "symbol": "BTC",
                "name": "Wrapped Bitcoin (Sollet)",
                "decimals": 6,
                "logoURI": "https://cdn.jsdelivr.net/gh/trustwallet/assets@master/blockchains/bitcoin/info/logo.png",
                "tags": ["wrapped-sollet", "ethereum"],
                "extensions": {
                    "bridgeContract": "https://etherscan.io/address/0xeae57ce9cc1984f202e15e038b964bb8bdf7229a",
                    "serumV3Usdc": "A8YFbxQYFVqKZaoYJLLUVcQiWP7G2MeEgW5wsAQgMvFw",
                    "serumV3Usdt": "C1EuT9VokAKLiW7i2ASnZUvxDoKuKkCpDDeNxAptuNe4",
                    "coingeckoId": "bitcoin",
                },
            },
            {
                "chainId": 101,
                "address": "2FPyTwcZLUg1MDrwsyoP4D6s1tM7hAkHYRjkNb5w6Pxk",
                "symbol": "ETH",
                "name": "Wrapped Ethereum (Sollet)",
                "decimals": 6,
                "logoURI": "https://cdn.jsdelivr.net/gh/trustwallet/assets@master/blockchains/ethereum/assets/0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2/logo.png",
                "tags": ["wrapped-sollet", "ethereum"],
                "extensions": {
                    "bridgeContract": "https://etherscan.io/address/0xeae57ce9cc1984f202e15e038b964bb8bdf7229a",
                    "serumV3Usdc": "4tSvZvnbyzHXLMTiFonMyxZoHmFqau1XArcRCVHLZ5gX",
                    "serumV3Usdt": "7dLVkUfBVfCGkFhSXDCq1ukM9usathSgS716t643iFGF",
                    "coingeckoId": "ethereum",
                },
            },
            {
                "chainId": 101,
                "address": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
                "symbol": "USDT",
                "name": "USDT",
                "decimals": 6,
                "logoURI": "https://cdn.jsdelivr.net/gh/solana-labs/explorer/public/tokens/usdt.svg",
                "tags": ["stablecoin"],
                "extensions": {
                    "website": "https://tether.to/",
                    "coingeckoId": "tether",
                },
            },
            {
                "chainId": 101,
                "address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                "symbol": "USDC",
                "name": "USD Coin",
                "decimals": 6,
                "logoURI": "https://cdn.jsdelivr.net/gh/solana-labs/token-list@main/assets/mainnet/EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v/logo.png",
                "tags": ["stablecoin"],
                "extensions": {
                    "website": "https://www.centre.io/",
                    "coingeckoId": "usd-coin",
                },
            },
        ]
    }
    actual = mango.SerumMarketLookup(fake_seeded_public_key("program ID"), data)
    assert actual is not None
    eth_usdt = actual.find_by_symbol("ETH/USDT")
    assert eth_usdt is not None
    assert eth_usdt.address == PublicKey("7dLVkUfBVfCGkFhSXDCq1ukM9usathSgS716t643iFGF")
    btc_usdc = actual.find_by_symbol("BTC/USDC")
    assert btc_usdc is not None
    assert btc_usdc.address == PublicKey("A8YFbxQYFVqKZaoYJLLUVcQiWP7G2MeEgW5wsAQgMvFw")


def test_serum_market_lookups_with_full_data() -> None:
    market_lookup = mango.SerumMarketLookup.load(
        fake_seeded_public_key("program ID"), mango.SPLTokenLookup.DefaultDataFilepath
    )
    srm_usdc = market_lookup.find_by_symbol("SRM/USDC")
    assert srm_usdc is not None
    assert srm_usdc.base.symbol == "SRM"
    assert srm_usdc.quote.symbol == "USDC"
    assert srm_usdc.address == PublicKey("ByRys5tuUWDgL73G8JBAEfkdFf8JWBzPBDHsBVQ5vbQA")

    btc_usdc = market_lookup.find_by_symbol("BTC/USDC")
    assert btc_usdc is not None
    assert btc_usdc.base.symbol == "BTC"
    assert btc_usdc.quote.symbol == "USDC"
    assert btc_usdc.address == PublicKey("A8YFbxQYFVqKZaoYJLLUVcQiWP7G2MeEgW5wsAQgMvFw")

    with disable_logging():
        non_existant_market = market_lookup.find_by_symbol("ETH/BTC")
    assert non_existant_market is None  # No such market


def test_serum_market_case_insensitive_lookups_with_full_data() -> None:
    market_lookup = mango.SerumMarketLookup.load(
        fake_seeded_public_key("program ID"), mango.SPLTokenLookup.DefaultDataFilepath
    )
    srm_usdc = market_lookup.find_by_symbol("srm/usdc")
    assert srm_usdc is not None
    assert srm_usdc.base.symbol == "SRM"
    assert srm_usdc.quote.symbol == "USDC"
    assert srm_usdc.address == PublicKey("ByRys5tuUWDgL73G8JBAEfkdFf8JWBzPBDHsBVQ5vbQA")


def test_overrides_with_full_data() -> None:
    market_lookup = mango.SerumMarketLookup.load(
        fake_seeded_public_key("program ID"), "./data/overrides.tokenlist.json"
    )
    eth_usdt = market_lookup.find_by_symbol("ETH/USDT")
    assert eth_usdt is not None
    assert eth_usdt.base.symbol == "ETH"
    assert eth_usdt.quote.symbol == "USDT"
    assert eth_usdt.address == PublicKey("7dLVkUfBVfCGkFhSXDCq1ukM9usathSgS716t643iFGF")

    eth_usdc = market_lookup.find_by_symbol("ETH/USDC")
    assert eth_usdc is not None
    assert eth_usdc.base.symbol == "ETH"
    assert eth_usdc.quote.symbol == "USDC"
    assert eth_usdc.address == PublicKey("4tSvZvnbyzHXLMTiFonMyxZoHmFqau1XArcRCVHLZ5gX")

    with disable_logging():
        non_existant_market = market_lookup.find_by_symbol("ETH/BTC")
    assert non_existant_market is None  # No such market


def test_compound_lookups_with_full_data() -> None:
    overrides = mango.SerumMarketLookup.load(
        fake_seeded_public_key("program ID"), "./data/overrides.tokenlist.json"
    )
    spl = mango.SerumMarketLookup.load(
        fake_seeded_public_key("program ID"), mango.SPLTokenLookup.DefaultDataFilepath
    )
    actual = mango.CompoundMarketLookup([overrides, spl])
    # actual should now find instruments in either overrides or spl
    eth_usdt = actual.find_by_symbol("ETH/USDT")
    assert eth_usdt is not None
    assert eth_usdt.base.symbol == "ETH"
    assert eth_usdt.quote.symbol == "USDT"
    assert eth_usdt.address == PublicKey("7dLVkUfBVfCGkFhSXDCq1ukM9usathSgS716t643iFGF")

    eth_usdc = actual.find_by_symbol("ETH/USDC")
    assert eth_usdc is not None
    assert eth_usdc.base.symbol == "ETH"
    assert eth_usdc.quote.symbol == "USDC"
    assert eth_usdc.address == PublicKey("4tSvZvnbyzHXLMTiFonMyxZoHmFqau1XArcRCVHLZ5gX")

    with disable_logging():
        srm_usdc = actual.find_by_symbol("SRM/USDC")
        assert srm_usdc is not None
        assert srm_usdc.base.symbol == "SRM"
        assert srm_usdc.quote.symbol == "USDC"
        assert srm_usdc.address == PublicKey(
            "ByRys5tuUWDgL73G8JBAEfkdFf8JWBzPBDHsBVQ5vbQA"
        )

        btc_usdc = actual.find_by_symbol("BTC/USDC")
        assert btc_usdc is not None
        assert btc_usdc.base.symbol == "BTC"
        assert btc_usdc.quote.symbol == "USDC"
        assert btc_usdc.address == PublicKey(
            "A8YFbxQYFVqKZaoYJLLUVcQiWP7G2MeEgW5wsAQgMvFw"
        )

        non_existant_market = actual.find_by_symbol("ETH/BTC")
        assert non_existant_market is None  # No such market
