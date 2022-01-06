import glob
import mango
import typing

from decimal import Decimal


def load_group(filename: str) -> mango.Group:
    account_info: mango.AccountInfo = mango.AccountInfo.load_json(filename)
    mainnet_token_lookup: mango.InstrumentLookup = mango.IdsJsonTokenLookup("mainnet", "mainnet.1")
    devnet_token_lookup: mango.InstrumentLookup = mango.IdsJsonTokenLookup("devnet", "devnet.2")
    devnet_non_spl_instrument_lookup: mango.InstrumentLookup = mango.NonSPLInstrumentLookup.load(
        mango.NonSPLInstrumentLookup.DefaultDevnetDataFilepath)
    instrument_lookup: mango.InstrumentLookup = mango.CompoundInstrumentLookup(
        [mainnet_token_lookup, devnet_token_lookup, devnet_non_spl_instrument_lookup])
    mainnet_market_lookup: mango.MarketLookup = mango.IdsJsonMarketLookup("mainnet", instrument_lookup)
    devnet_market_lookup: mango.MarketLookup = mango.IdsJsonMarketLookup("devnet", instrument_lookup)
    market_lookup: mango.MarketLookup = mango.CompoundMarketLookup([mainnet_market_lookup, devnet_market_lookup])
    return mango.Group.parse(account_info, "devnet.2", instrument_lookup, market_lookup)


def load_account(filename: str, group: mango.Group, cache: mango.Cache) -> mango.Account:
    account_info: mango.AccountInfo = mango.AccountInfo.load_json(filename)
    return mango.Account.parse(account_info, group, cache)


def load_openorders(filename: str) -> mango.OpenOrders:
    account_info: mango.AccountInfo = mango.AccountInfo.load_json(filename)
    # Just hard-code the decimals for now.
    return mango.OpenOrders.parse(account_info, Decimal(6), Decimal(6))


def load_cache(filename: str) -> mango.Cache:
    account_info: mango.AccountInfo = mango.AccountInfo.load_json(filename)
    return mango.Cache.parse(account_info)


def load_root_bank(filename: str) -> mango.RootBank:
    account_info: mango.AccountInfo = mango.AccountInfo.load_json(filename)
    return mango.RootBank.parse(account_info)


def load_node_bank(filename: str) -> mango.NodeBank:
    account_info: mango.AccountInfo = mango.AccountInfo.load_json(filename)
    return mango.NodeBank.parse(account_info)


def load_data_from_directory(directory_path: str) -> typing.Tuple[mango.Group, mango.Cache, mango.Account, typing.Dict[str, mango.OpenOrders]]:
    all_openorders = {}
    for filepath in glob.iglob(f"{directory_path}/openorders*.json"):
        openorders = load_openorders(filepath)
        all_openorders[str(openorders.address)] = openorders
    cache = load_cache(f"{directory_path}/cache.json")
    group = load_group(f"{directory_path}/group.json")
    account = load_account(f"{directory_path}/account.json", group, cache)

    return group, cache, account, all_openorders
