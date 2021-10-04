import glob
import mango
import typing

from decimal import Decimal


def data_group(filename: str, root_banks: typing.Sequence[mango.RootBank]) -> mango.Group:
    account_info: mango.AccountInfo = mango.AccountInfo.load_json(filename)
    mainnet_token_lookup: mango.TokenLookup = mango.IdsJsonTokenLookup("mainnet", "mainnet.1")
    devnet_token_lookup: mango.TokenLookup = mango.IdsJsonTokenLookup("devnet", "devnet.2")
    token_lookup: mango.TokenLookup = mango.CompoundTokenLookup([mainnet_token_lookup, devnet_token_lookup])
    return mango.Group.parse_locally(account_info, "devnet.2", root_banks, token_lookup)


def data_account(filename: str, group: mango.Group) -> mango.Account:
    account_info: mango.AccountInfo = mango.AccountInfo.load_json(filename)
    return mango.Account.parse(account_info, group)


def data_openorders(filename: str) -> mango.OpenOrders:
    account_info: mango.AccountInfo = mango.AccountInfo.load_json(filename)
    # Just hard-code the decimals for now.
    return mango.OpenOrders.parse(account_info, Decimal(6), Decimal(6))


def data_cache(filename: str) -> mango.Cache:
    account_info: mango.AccountInfo = mango.AccountInfo.load_json(filename)
    return mango.Cache.parse(account_info)


def data_root_bank(filename: str) -> mango.RootBank:
    account_info: mango.AccountInfo = mango.AccountInfo.load_json(filename)
    return mango.RootBank.parse(account_info)


def load_data_from_directory(directory_path: str) -> typing.Tuple[mango.Group, mango.Cache, mango.Account, typing.Dict[str, mango.OpenOrders]]:
    root_banks = []
    for filepath in glob.iglob(f"{directory_path}/root_bank*.json"):
        root_bank = data_root_bank(filepath)
        root_banks += [root_bank]
    all_openorders = {}
    for filepath in glob.iglob(f"{directory_path}/openorders*.json"):
        openorders = data_openorders(filepath)
        all_openorders[str(openorders.address)] = openorders
    group = data_group(f"{directory_path}/group.json", root_banks)
    account = data_account(f"{directory_path}/account.json", group)
    cache = data_cache(f"{directory_path}/cache.json")

    return group, cache, account, all_openorders
