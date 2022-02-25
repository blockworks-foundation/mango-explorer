from .context import mango

from solana.publickey import PublicKey


def test_spl_token_lookup() -> None:
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
            },
        ]
    }
    actual = mango.SPLTokenLookup("test-filename", data)
    assert actual is not None
    eth = actual.find_by_symbol("ETH")
    assert eth is not None
    assert eth.name == "Wrapped Ethereum (Sollet)"
    btc = actual.find_by_symbol("BTC")
    assert btc is not None
    assert btc.name == "Wrapped Bitcoin (Sollet)"
    usdc = actual.find_by_symbol("usDC")
    assert usdc is not None
    assert usdc.name == "USD Coin"


def test_spl_token_lookups_with_full_data() -> None:
    actual = mango.SPLTokenLookup.load(mango.SPLTokenLookup.DefaultDataFilepath)
    btc = actual.find_by_symbol("BTC")
    assert btc is not None
    assert btc.mint == PublicKey("9n4nbM75f5Ui33ZbPYXn59EwSgE8CGsHtAeTH5YFeJ9E")
    srm = actual.find_by_mint(PublicKey("AKJHspCwDhABucCxNLXUSfEzb7Ny62RqFtC9uNjJi4fq"))
    assert srm is not None
    assert srm.symbol == "SRM-SOL"
    usdt = actual.find_by_mint(
        PublicKey("Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB")
    )
    assert usdt is not None
    assert usdt.symbol == "USDT"


def test_override_lookups_with_full_data() -> None:
    actual = mango.SPLTokenLookup.load("./data/overrides.tokenlist.json")
    eth = actual.find_by_symbol("ETH")
    assert eth is not None
    assert eth.mint == PublicKey("2FPyTwcZLUg1MDrwsyoP4D6s1tM7hAkHYRjkNb5w6Pxk")
    usdt = actual.find_by_mint(
        PublicKey("Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB")
    )
    assert usdt is not None
    assert usdt.symbol == "USDT"


def test_compound_lookups_with_full_data() -> None:
    overrides = mango.SPLTokenLookup.load("./data/overrides.tokenlist.json")
    spl = mango.SPLTokenLookup.load(mango.SPLTokenLookup.DefaultDataFilepath)
    actual = mango.CompoundInstrumentLookup([overrides, spl])
    # actual should now find instruments in either overrides or spl
    eth = actual.find_by_symbol("ETH")
    assert eth is not None
    assert isinstance(eth, mango.Token)
    assert eth.mint == PublicKey("2FPyTwcZLUg1MDrwsyoP4D6s1tM7hAkHYRjkNb5w6Pxk")
    btc = actual.find_by_symbol("BTC")
    assert btc is not None
    assert isinstance(btc, mango.Token)
    assert btc.mint == PublicKey("9n4nbM75f5Ui33ZbPYXn59EwSgE8CGsHtAeTH5YFeJ9E")
    srm = actual.find_by_mint(PublicKey("AKJHspCwDhABucCxNLXUSfEzb7Ny62RqFtC9uNjJi4fq"))
    assert srm is not None
    assert isinstance(srm, mango.Token)
    assert srm.symbol == "SRM-SOL"
    usdt = actual.find_by_mint(
        PublicKey("Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB")
    )
    assert usdt is not None
    assert isinstance(usdt, mango.Token)
    assert usdt.symbol == "USDT"


def test_all_expected_v3_instruments() -> None:
    def check_expected(symbol: str, pubkey: str) -> None:
        token = actual.find_by_symbol(symbol)
        assert token is not None
        assert isinstance(token, mango.Token)
        assert token.mint == PublicKey(pubkey)

    # Load all token data the same order the ContextBuilder loads them:
    # instrument_lookup = CompoundInstrumentLookup(
    #     [
    #         ids_json_token_lookup,
    #         mainnet_overrides_token_lookup,
    #         mainnet_non_spl_instrument_lookup,
    #         mainnet_spl_token_lookup,
    #     ]
    # )
    idsjson = mango.IdsJsonTokenLookup("mainnet", "mainnet.1")
    overrides = mango.SPLTokenLookup.load("./data/overrides.tokenlist.json")
    spl = mango.SPLTokenLookup.load(mango.SPLTokenLookup.DefaultDataFilepath)
    non_spl = mango.NonSPLInstrumentLookup.load(
        mango.NonSPLInstrumentLookup.DefaultMainnetDataFilepath
    )
    actual = mango.CompoundInstrumentLookup([idsjson, overrides, non_spl, spl])
    # actual should now find instruments in either overrides or spl
    check_expected("USDC", "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")
    check_expected("MNGO", "MangoCzJ36AjZyKwVj3VnYU4GTonjfVEnJmvvWaxLac")
    check_expected("BTC", "9n4nbM75f5Ui33ZbPYXn59EwSgE8CGsHtAeTH5YFeJ9E")
    check_expected("ETH", "2FPyTwcZLUg1MDrwsyoP4D6s1tM7hAkHYRjkNb5w6Pxk")
    check_expected("SOL", "So11111111111111111111111111111111111111112")
    check_expected("USDT", "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB")
    check_expected("SRM", "SRMuApVNdxXokk5GT7XD5cUUgXMBCoAz2LHeuAoKWRt")
    check_expected("RAY", "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R")
    check_expected("COPE", "8HGyAAB1yoM1ttS7pXjHMa3dukTFGQggnFFH3hJZgzQh")
    check_expected("FTT", "AGFEad2et2ZJif9jaGpdMixQqvW5i81aBdvKe7PHNfz3")
    check_expected("MSOL", "mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So")
    check_expected("BNB", "9gP2kCy3wA1ctvYWQk75guqXuHfrEomqydHLtcTCqiLa")
    check_expected("AVAX", "KgV1GvrHQmRBY8sHQQeUKwTm2r2h8t4C8qt12Cw1HVE")
    check_expected("LUNA", "F6v4wfAdJB8D8p77bMXZgYt8TDKsYxLYxH5AFhUkYx9W")
