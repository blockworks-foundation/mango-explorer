# # ⚠ Warning
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
# LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN
# NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# [🥭 Mango Markets](https://mango.markets/) support is available at:
#   [Docs](https://docs.mango.markets/)
#   [Discord](https://discord.gg/67jySBhxrg)
#   [Twitter](https://twitter.com/mangomarkets)
#   [Github](https://github.com/blockworks-foundation)
#   [Email](mailto:hello@blockworks.foundation)

import typing

from decimal import Decimal
from solana.publickey import PublicKey
from solana.rpc.types import MemcmpOpts

from .accountinfo import AccountInfo
from .addressableaccount import AddressableAccount
from .context import Context
from .encoding import encode_key
from .group import Group
from .layouts import layouts
from .metadata import Metadata
from .tokenvalue import TokenValue
from .version import Version

# # 🥭 Account class
#
# `Account` holds information about the account for a particular user/wallet for a particualr `Group`.
#


class Account(AddressableAccount):
    def __init__(self, account_info: AccountInfo, version: Version,
                 meta_data: Metadata, group: Group, owner: PublicKey, in_basket: typing.Sequence[Decimal],
                 deposits: typing.Sequence[typing.Optional[TokenValue]], borrows: typing.Sequence[typing.Optional[TokenValue]],
                 net_assets: typing.Sequence[typing.Optional[TokenValue]], spot_open_orders: typing.Sequence[PublicKey],
                 perp_accounts: typing.Sequence[typing.Any], is_bankrupt: bool):
        super().__init__(account_info)
        self.version: Version = version

        self.meta_data: Metadata = meta_data
        self.group: Group = group
        self.owner: PublicKey = owner
        self.in_basket: typing.Sequence[Decimal] = in_basket
        self.deposits: typing.Sequence[typing.Optional[TokenValue]] = deposits
        self.borrows: typing.Sequence[typing.Optional[TokenValue]] = borrows
        self.net_assets: typing.Sequence[typing.Optional[TokenValue]] = net_assets
        self.spot_open_orders: typing.Sequence[PublicKey] = spot_open_orders
        self.perp_accounts: typing.Sequence[layouts.PERP_ACCOUNT] = perp_accounts
        self.is_bankrupt: bool = is_bankrupt

    @staticmethod
    def from_layout(layout: layouts.MANGO_ACCOUNT, account_info: AccountInfo, version: Version, group: Group) -> "Account":
        meta_data = Metadata.from_layout(layout.meta_data)
        owner: PublicKey = layout.owner
        in_basket: typing.Sequence[Decimal] = layout.in_basket
        deposits: typing.List[typing.Optional[TokenValue]] = []
        borrows: typing.List[typing.Optional[TokenValue]] = []
        net_assets: typing.List[typing.Optional[TokenValue]] = []
        for index, token_info in enumerate(group.tokens):
            if token_info:
                intrinsic_deposit = token_info.root_bank.deposit_index * layout.deposits[index]
                deposit = token_info.token.shift_to_decimals(intrinsic_deposit)
                deposits += [TokenValue(token_info.token, deposit)]
                intrinsic_borrow = token_info.root_bank.borrow_index * layout.borrows[index]
                borrow = token_info.token.shift_to_decimals(intrinsic_borrow)
                borrows += [TokenValue(token_info.token, borrow)]
                net_assets += [TokenValue(token_info.token, deposit - borrow)]
            else:
                deposits += [None]
                borrows += [None]
                net_assets += [None]

        spot_open_orders: typing.Sequence[PublicKey] = layout.spot_open_orders
        perp_accounts: typing.Sequence[typing.Any] = layout.perp_accounts
        is_bankrupt: bool = layout.is_bankrupt

        return Account(account_info, version, meta_data, group, owner, in_basket, deposits, borrows, net_assets, spot_open_orders, perp_accounts, is_bankrupt)

    @staticmethod
    def parse(context: Context, account_info: AccountInfo, group: Group) -> "Account":
        data = account_info.data
        if len(data) != layouts.MANGO_ACCOUNT.sizeof():
            raise Exception(
                f"Account data length ({len(data)}) does not match expected size ({layouts.MANGO_ACCOUNT.sizeof()}")

        layout = layouts.MANGO_ACCOUNT.parse(data)
        return Account.from_layout(layout, account_info, Version.V1, group)

    @staticmethod
    def load(context: Context, address: PublicKey, group: Group) -> "Account":
        account_info = AccountInfo.load(context, address)
        if account_info is None:
            raise Exception(f"Account account not found at address '{address}'")
        return Account.parse(context, account_info, group)

    @staticmethod
    def load_all_for_owner(context: Context, owner: PublicKey, group: Group) -> typing.Sequence["Account"]:
        # mango_group is just after the METADATA, which is the first entry.
        group_offset = layouts.METADATA.sizeof()
        # owner is just after mango_group in the layout, and it's a PublicKey which is 32 bytes.
        owner_offset = group_offset + 32
        filters = [
            MemcmpOpts(
                offset=group_offset,
                bytes=encode_key(group.address)
            ),
            MemcmpOpts(
                offset=owner_offset,
                bytes=encode_key(owner)
            )
        ]

        response = context.client.get_program_accounts(
            context.program_id, memcmp_opts=filters, commitment=context.commitment, encoding="base64")
        accounts = []
        for account_data in response["result"]:
            address = PublicKey(account_data["pubkey"])
            account_info = AccountInfo._from_response_values(account_data["account"], address)
            account = Account.parse(context, account_info, group)
            accounts += [account]
        return accounts

    def __str__(self):
        deposits = "\n        ".join(
            [f"{deposit}" for deposit in self.deposits if deposit.value != Decimal(0)] or ["None"])
        borrows = "\n        ".join([f"{borrow}" for borrow in self.borrows if borrow.value != Decimal(0)] or ["None"])
        net_assets = "\n        ".join(
            [f"{net_asset}" for net_asset in self.net_assets if net_asset.value != Decimal(0)] or ["None"])
        spot_open_orders = ", ".join([f"{oo}" for oo in self.spot_open_orders if oo is not None])
        perp_accounts = ", ".join(
            [f"{perp}".replace("\n", "\n        ") for perp in self.perp_accounts if perp.open_orders.is_free_bits != 0xFFFFFFFF])
        group = f"{self.group}".replace("\n", "\n        ")
        return f"""« 𝙰𝚌𝚌𝚘𝚞𝚗𝚝 {self.version} [{self.address}]
    {self.meta_data}
    Owner: {self.owner}
        {group}
    Deposits:
        {deposits}
    Borrows:
        {borrows}
    Net Assets:
        {net_assets}
    Spot Open Orders:
        {spot_open_orders}
    Perp Accounts:
        {perp_accounts}
»"""
