import glob
import mango
import os.path
import typing


def instrument_lookup_mainnet() -> mango.InstrumentLookup:
    mainnet_token_lookup: mango.InstrumentLookup = mango.IdsJsonTokenLookup(
        "mainnet", "mainnet.1"
    )

    mainnet_overrides_filename = os.path.join(
        mango.DATA_PATH, "overrides.tokenlist.json"
    )
    mainnet_overrides_token_lookup: mango.InstrumentLookup = mango.SPLTokenLookup.load(
        mainnet_overrides_filename
    )
    mainnet_non_spl_instrument_lookup: mango.InstrumentLookup = (
        mango.NonSPLInstrumentLookup.load(
            mango.NonSPLInstrumentLookup.DefaultMainnetDataFilepath
        )
    )

    return mango.CompoundInstrumentLookup(
        [
            mainnet_overrides_token_lookup,
            mainnet_token_lookup,
            mainnet_non_spl_instrument_lookup,
        ]
    )


def instrument_lookup_devnet() -> mango.InstrumentLookup:
    devnet_token_lookup: mango.InstrumentLookup = mango.IdsJsonTokenLookup(
        "devnet", "devnet.2"
    )

    devnet_overrides_filename = os.path.join(
        mango.DATA_PATH, "overrides.tokenlist.devnet.json"
    )
    devnet_overrides_token_lookup: mango.InstrumentLookup = mango.SPLTokenLookup.load(
        devnet_overrides_filename
    )
    devnet_non_spl_instrument_lookup: mango.InstrumentLookup = (
        mango.NonSPLInstrumentLookup.load(
            mango.NonSPLInstrumentLookup.DefaultDevnetDataFilepath
        )
    )

    return mango.CompoundInstrumentLookup(
        [
            devnet_overrides_token_lookup,
            devnet_token_lookup,
            devnet_non_spl_instrument_lookup,
        ]
    )


def instrument_lookup() -> mango.InstrumentLookup:
    return mango.CompoundInstrumentLookup(
        [instrument_lookup_mainnet(), instrument_lookup_devnet()]
    )


def market_lookup_mainnet() -> mango.MarketLookup:
    return mango.IdsJsonMarketLookup("mainnet", instrument_lookup_mainnet())


def market_lookup_devnet() -> mango.MarketLookup:
    return mango.IdsJsonMarketLookup("devnet", instrument_lookup_devnet())


def market_lookup() -> mango.MarketLookup:
    return mango.CompoundMarketLookup([market_lookup_mainnet(), market_lookup_devnet()])


def load_group(filename: str) -> mango.Group:
    account_info: mango.AccountInfo = mango.AccountInfo.load_json(filename)
    instruments: mango.InstrumentLookup = instrument_lookup()
    markets: mango.MarketLookup = market_lookup()
    return mango.Group.parse(account_info, "devnet.2", instruments, markets)


def load_account(
    filename: str, group: mango.Group, cache: mango.Cache
) -> mango.Account:
    account_info: mango.AccountInfo = mango.AccountInfo.load_json(filename)
    return mango.Account.parse(account_info, group, cache)


def load_openorders(filename: str) -> mango.OpenOrders:
    account_info: mango.AccountInfo = mango.AccountInfo.load_json(filename)
    parsed = mango.layouts.OPEN_ORDERS.parse(account_info.data)
    markets: mango.MarketLookup = market_lookup()
    market = markets.find_by_address(parsed.market)
    if market is None:
        raise Exception(f"Could not find market metadata for {parsed.market}")

    return mango.OpenOrders.parse(
        account_info, mango.Token.ensure(market.base), market.quote
    )


def load_cache(filename: str) -> mango.Cache:
    account_info: mango.AccountInfo = mango.AccountInfo.load_json(filename)
    return mango.Cache.parse(account_info)


def load_root_bank(filename: str) -> mango.RootBank:
    account_info: mango.AccountInfo = mango.AccountInfo.load_json(filename)
    return mango.RootBank.parse(account_info)


def load_node_bank(filename: str) -> mango.NodeBank:
    account_info: mango.AccountInfo = mango.AccountInfo.load_json(filename)
    return mango.NodeBank.parse(account_info)


def load_data_from_directory(
    directory_path: str,
) -> typing.Tuple[
    mango.Group, mango.Cache, mango.Account, typing.Dict[str, mango.OpenOrders]
]:
    all_openorders = {}
    for filepath in glob.iglob(f"{directory_path}/openorders*.json"):
        openorders = load_openorders(filepath)
        all_openorders[str(openorders.address)] = openorders
    cache = load_cache(f"{directory_path}/cache.json")
    group = load_group(f"{directory_path}/group.json")
    account = load_account(f"{directory_path}/account.json", group, cache)

    return group, cache, account, all_openorders
