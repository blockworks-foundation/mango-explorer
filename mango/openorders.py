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
from pyserum.open_orders_account import OpenOrdersAccount
from solana.publickey import PublicKey
from solana.rpc.types import MemcmpOpts

from .accountinfo import AccountInfo
from .addressableaccount import AddressableAccount
from .context import Context
from .encoding import encode_key
from .group import Group
from .layouts import layouts
from .serumaccountflags import SerumAccountFlags
from .version import Version

# # 🥭 OpenOrders class
#


class OpenOrders(AddressableAccount):
    def __init__(self, account_info: AccountInfo, version: Version, program_id: PublicKey,
                 account_flags: SerumAccountFlags, market: PublicKey, owner: PublicKey,
                 base_token_free: Decimal, base_token_total: Decimal, quote_token_free: Decimal,
                 quote_token_total: Decimal, free_slot_bits: Decimal, is_bid_bits: Decimal,
                 orders: typing.List[Decimal], client_ids: typing.List[Decimal],
                 referrer_rebate_accrued: Decimal):
        super().__init__(account_info)
        self.version: Version = version
        self.program_id: PublicKey = program_id
        self.account_flags: SerumAccountFlags = account_flags
        self.market: PublicKey = market
        self.owner: PublicKey = owner
        self.base_token_free: Decimal = base_token_free
        self.base_token_total: Decimal = base_token_total
        self.quote_token_free: Decimal = quote_token_free
        self.quote_token_total: Decimal = quote_token_total
        self.free_slot_bits: Decimal = free_slot_bits
        self.is_bid_bits: Decimal = is_bid_bits
        self.orders: typing.List[Decimal] = orders
        self.client_ids: typing.List[Decimal] = client_ids
        self.referrer_rebate_accrued: Decimal = referrer_rebate_accrued

    # Sometimes pyserum wants to take its own OpenOrdersAccount as a parameter (e.g. in settle_funds())
    def to_pyserum(self) -> OpenOrdersAccount:
        return OpenOrdersAccount.from_bytes(self.address, self.account_info.data)

    @staticmethod
    def from_layout(layout: layouts.OPEN_ORDERS, account_info: AccountInfo,
                    base_decimals: Decimal, quote_decimals: Decimal) -> "OpenOrders":
        account_flags = SerumAccountFlags.from_layout(layout.account_flags)
        program_id = account_info.owner

        base_divisor = 10 ** base_decimals
        quote_divisor = 10 ** quote_decimals
        base_token_free: Decimal = layout.base_token_free / base_divisor
        base_token_total: Decimal = layout.base_token_total / base_divisor
        quote_token_free: Decimal = layout.quote_token_free / quote_divisor
        quote_token_total: Decimal = layout.quote_token_total / quote_divisor
        referrer_rebate_accrued: Decimal = layout.referrer_rebate_accrued / quote_divisor
        nonzero_orders: typing.List[Decimal] = list([order for order in layout.orders if order != 0])
        nonzero_client_ids: typing.List[Decimal] = list(
            [client_id for client_id in layout.client_ids if client_id != 0])

        return OpenOrders(account_info, Version.UNSPECIFIED, program_id, account_flags, layout.market,
                          layout.owner, base_token_free, base_token_total, quote_token_free, quote_token_total,
                          layout.free_slot_bits, layout.is_bid_bits, nonzero_orders, nonzero_client_ids,
                          referrer_rebate_accrued)

    @staticmethod
    def parse(account_info: AccountInfo, base_decimals: Decimal, quote_decimals: Decimal) -> "OpenOrders":
        data = account_info.data
        if len(data) != layouts.OPEN_ORDERS.sizeof():
            raise Exception(f"Data length ({len(data)}) does not match expected size ({layouts.OPEN_ORDERS.sizeof()})")

        layout = layouts.OPEN_ORDERS.parse(data)
        return OpenOrders.from_layout(layout, account_info, base_decimals, quote_decimals)

    @staticmethod
    def load_raw_open_orders_account_infos(context: Context, group: Group) -> typing.Dict[str, AccountInfo]:
        filters = [
            MemcmpOpts(
                offset=layouts.SERUM_ACCOUNT_FLAGS.sizeof() + 37,
                bytes=encode_key(group.signer_key)
            )
        ]

        results = context.client.get_program_accounts(
            group.dex_program_id, data_size=layouts.OPEN_ORDERS.sizeof(), memcmp_opts=filters)
        account_infos = list(map(lambda pair: AccountInfo._from_response_values(pair[0], pair[1]), [
                             (result["account"], PublicKey(result["pubkey"])) for result in results]))
        account_infos_by_address = {key: value for key, value in [
            (str(account_info.address), account_info) for account_info in account_infos]}
        return account_infos_by_address

    @staticmethod
    def load(context: Context, address: PublicKey, base_decimals: Decimal, quote_decimals: Decimal) -> "OpenOrders":
        open_orders_account = AccountInfo.load(context, address)
        if open_orders_account is None:
            raise Exception(f"OpenOrders account not found at address '{address}'")
        return OpenOrders.parse(open_orders_account, base_decimals, quote_decimals)

    @staticmethod
    def load_for_market_and_owner(context: Context, market: PublicKey, owner: PublicKey, program_id: PublicKey, base_decimals: Decimal, quote_decimals: Decimal):
        filters = [
            MemcmpOpts(
                offset=layouts.SERUM_ACCOUNT_FLAGS.sizeof() + 5,
                bytes=encode_key(market)
            ),
            MemcmpOpts(
                offset=layouts.SERUM_ACCOUNT_FLAGS.sizeof() + 37,
                bytes=encode_key(owner)
            )
        ]

        results = context.client.get_program_accounts(
            program_id, data_size=layouts.OPEN_ORDERS.sizeof(), memcmp_opts=filters)
        accounts = list(map(lambda pair: AccountInfo._from_response_values(pair[0], pair[1]), [
                        (result["account"], PublicKey(result["pubkey"])) for result in results]))
        return list(map(lambda acc: OpenOrders.parse(acc, base_decimals, quote_decimals), accounts))

    def __str__(self) -> str:
        orders = ", ".join(map(str, self.orders)) or "None"
        client_ids = ", ".join(map(str, self.client_ids)) or "None"

        return f"""« OpenOrders [{self.address}]:
    Flags: {self.account_flags}
    Program ID: {self.program_id}
    Market: {self.market}
    Owner: {self.owner}
    Base Token: {self.base_token_free:,.8f} of {self.base_token_total:,.8f}
    Quote Token: {self.quote_token_free:,.8f} of {self.quote_token_total:,.8f}
    Referrer Rebate Accrued: {self.referrer_rebate_accrued}
    Orders:
        {orders}
    Client IDs:
        {client_ids}
»"""
