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
from .layouts import layouts
from .mangogroup import MangoGroup
from .metadata import Metadata
from .version import Version

# # 🥭 MangoAccount class
#
# `MangoAccount` holds information about the account for a particular user/wallet for a particualr `MangoGroup`.
#


class MangoAccount(AddressableAccount):
    def __init__(self, account_info: AccountInfo, version: Version,
                 meta_data: Metadata, group: PublicKey, owner: PublicKey, in_basket: typing.List[Decimal],
                 deposits: typing.List[Decimal], borrows: typing.List[Decimal],
                 spot_open_orders: typing.List[PublicKey], perp_accounts: typing.List[typing.Any]):
        super().__init__(account_info)
        self.version: Version = version

        self.meta_data: Metadata = meta_data
        self.group: PublicKey = group
        self.owner: PublicKey = owner
        self.in_basket: typing.List[Decimal] = in_basket
        self.deposits: typing.List[Decimal] = deposits
        self.borrows: typing.List[Decimal] = borrows
        self.spot_open_orders: typing.List[PublicKey] = spot_open_orders
        self.perp_accounts: typing.List[layouts.PERP_ACCOUNT] = perp_accounts

    @staticmethod
    def from_layout(layout: layouts.MANGO_ACCOUNT, account_info: AccountInfo, version: Version) -> "MangoAccount":
        meta_data = Metadata.from_layout(layout.meta_data)
        group: PublicKey = layout.group
        owner: PublicKey = layout.owner
        in_basket: typing.List[Decimal] = layout.in_basket
        deposits: typing.List[Decimal] = layout.deposits
        borrows: typing.List[Decimal] = layout.borrows
        spot_open_orders: typing.List[PublicKey] = layout.spot_open_orders
        perp_accounts: typing.List[typing.Any] = layout.perp_accounts

        return MangoAccount(account_info, version, meta_data, group, owner, in_basket, deposits, borrows, spot_open_orders, perp_accounts)

    @staticmethod
    def parse(context: Context, account_info: AccountInfo) -> "MangoAccount":
        data = account_info.data
        if len(data) != layouts.MANGO_ACCOUNT.sizeof():
            raise Exception(
                f"MangoAccount data length ({len(data)}) does not match expected size ({layouts.MANGO_ACCOUNT.sizeof()}")

        layout = layouts.MANGO_ACCOUNT.parse(data)
        return MangoAccount.from_layout(layout, account_info, Version.V1)

    @staticmethod
    def load(context: Context, address: PublicKey) -> "MangoAccount":
        account_info = AccountInfo.load(context, address)
        if account_info is None:
            raise Exception(f"MangoAccount account not found at address '{address}'")
        return MangoAccount.parse(context, account_info)

    @staticmethod
    def load_all_for_owner(context: Context, owner: PublicKey, group: MangoGroup) -> typing.List["MangoAccount"]:
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
            account = MangoAccount.parse(context, account_info)
            accounts += [account]
        return accounts

    def __str__(self):
        in_baskets = ", ".join([f"{in_basket}" for in_basket in self.in_basket])
        deposits = ", ".join([f"{deposit}" for deposit in self.deposits])
        borrows = ", ".join([f"{borrow}" for borrow in self.borrows])
        spot_open_orders = ", ".join([f"{oo}" for oo in self.spot_open_orders if oo is not None])
        perp_accounts = ", ".join(
            [f"{perp}" for perp in self.perp_accounts if perp.open_orders.is_free_bits != 0xFFFFFFFF])
        return f"""« 𝙼𝚎𝚛𝚙𝚜𝙰𝚌𝚌𝚘𝚞𝚗𝚝 {self.version} [{self.address}]
    {self.meta_data}
    Owner: {self.owner}
    Group: {self.group}
    In Basket:
        {in_baskets}
    Deposits:
        {deposits}
    Borrows:
        {borrows}
    Spot Open Orders:
        {spot_open_orders}
    Perp Accounts:
        {perp_accounts}
»"""
