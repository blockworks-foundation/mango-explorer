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


import construct
import logging
import time
import typing

from decimal import Decimal
from solana.publickey import PublicKey
from solana.rpc.types import MemcmpOpts

from .accountinfo import AccountInfo
from .addressableaccount import AddressableAccount
from .balancesheet import BalanceSheet
from .constants import SYSTEM_PROGRAM_ADDRESS
from .context import Context
from .encoding import encode_int, encode_key
from .group import Group
from .layouts import layouts
from .mangoaccountflags import MangoAccountFlags
from .openorders import OpenOrders
from .token import Token
from .tokenvalue import TokenValue
from .version import Version

# # 🥭 MarginAccount class
#


class MarginAccount(AddressableAccount):
    def __init__(self, account_info: AccountInfo, version: Version, account_flags: MangoAccountFlags,
                 has_borrows: bool, mango_group: PublicKey, owner: PublicKey, being_liquidated: bool,
                 deposits: typing.List[TokenValue], borrows: typing.List[TokenValue],
                 open_orders: typing.List[typing.Optional[PublicKey]]):
        super().__init__(account_info)
        self.version: Version = version
        self.account_flags: MangoAccountFlags = account_flags
        self.has_borrows: bool = has_borrows
        self.mango_group: PublicKey = mango_group
        self.owner: PublicKey = owner
        self.being_liquidated: bool = being_liquidated
        self.deposits: typing.List[TokenValue] = deposits
        self.borrows: typing.List[TokenValue] = borrows
        self.open_orders: typing.List[typing.Optional[PublicKey]] = open_orders
        self.open_orders_accounts: typing.List[typing.Optional[OpenOrders]] = [None] * len(open_orders)

    @staticmethod
    def from_layout(layout: construct.Struct, account_info: AccountInfo, version: Version, group: Group) -> "MarginAccount":
        if group.address != layout.mango_group:
            raise Exception(
                f"Margin account belongs to Group ID '{group.address}', not Group ID '{layout.mango_group}'")

        if version == Version.V1:
            # This is an old-style margin account, with no borrows flag
            has_borrows = False
        else:
            # This is a new-style margin account where we can depend on the presence of the borrows flag
            has_borrows = bool(layout.has_borrows)

        account_flags: MangoAccountFlags = MangoAccountFlags.from_layout(layout.account_flags)
        deposits: typing.List[TokenValue] = []
        for index, deposit in enumerate(layout.deposits):
            token = group.basket_tokens[index].token
            rebased_deposit = deposit * group.basket_tokens[index].index.deposit.value
            token_value = TokenValue(token, rebased_deposit)
            deposits += [token_value]

        borrows: typing.List[TokenValue] = []
        for index, borrow in enumerate(layout.borrows):
            token = group.basket_tokens[index].token
            rebased_borrow = borrow * group.basket_tokens[index].index.borrow.value
            token_value = TokenValue(token, rebased_borrow)
            borrows += [token_value]

        return MarginAccount(account_info, version, account_flags, has_borrows, layout.mango_group,
                             layout.owner, layout.being_liquidated, deposits, borrows, list(layout.open_orders))

    @staticmethod
    def parse(account_info: AccountInfo, group: Group) -> "MarginAccount":
        data = account_info.data
        if len(data) == layouts.MARGIN_ACCOUNT_V1.sizeof():
            layout = layouts.MARGIN_ACCOUNT_V1.parse(data)
            version: Version = Version.V1
        elif len(data) == layouts.MARGIN_ACCOUNT_V2.sizeof():
            version = Version.V2
            layout = layouts.MARGIN_ACCOUNT_V2.parse(data)
        else:
            raise Exception(
                f"Data length ({len(data)}) does not match expected size ({layouts.MARGIN_ACCOUNT_V1.sizeof()} or {layouts.MARGIN_ACCOUNT_V2.sizeof()})")

        return MarginAccount.from_layout(layout, account_info, version, group)

    @staticmethod
    def load(context: Context, margin_account_address: PublicKey, group: Group) -> "MarginAccount":
        account_info = AccountInfo.load(context, margin_account_address)
        if account_info is None:
            raise Exception(f"MarginAccount account not found at address '{margin_account_address}'")

        margin_account = MarginAccount.parse(account_info, group)
        margin_account.load_open_orders_accounts(context, group)
        return margin_account

    @staticmethod
    def load_all_for_group(context: Context, program_id: PublicKey, group: Group) -> typing.List["MarginAccount"]:
        filters = [
            MemcmpOpts(
                offset=layouts.MANGO_ACCOUNT_FLAGS.sizeof(),  # mango_group is just after the MangoAccountFlags, which is the first entry
                bytes=encode_key(group.address)
            )
        ]

        if group.version == Version.V1:
            parser = layouts.MARGIN_ACCOUNT_V1
        else:
            parser = layouts.MARGIN_ACCOUNT_V2

        response = context.client.get_program_accounts(
            program_id, data_size=parser.sizeof(), memcmp_opts=filters, commitment=context.commitment, encoding="base64")
        margin_accounts = []
        for margin_account_data in response["result"]:
            address = PublicKey(margin_account_data["pubkey"])
            account = AccountInfo._from_response_values(margin_account_data["account"], address)
            margin_account = MarginAccount.parse(account, group)
            margin_accounts += [margin_account]
        return margin_accounts

    @staticmethod
    def load_all_for_group_with_open_orders(context: Context, program_id: PublicKey, group: Group) -> typing.List["MarginAccount"]:
        margin_accounts = MarginAccount.load_all_for_group(context, program_id, group)
        open_orders = OpenOrders.load_raw_open_orders_account_infos(context, group)
        for margin_account in margin_accounts:
            margin_account.install_open_orders_accounts(group, open_orders)

        return margin_accounts

    @staticmethod
    def load_all_for_owner(context: Context, owner: PublicKey, group: typing.Optional[Group] = None) -> typing.List["MarginAccount"]:
        if group is None:
            group = Group.load(context)

        # mango_group is just after the MangoAccountFlags, which is the first entry.
        mango_group_offset = layouts.MANGO_ACCOUNT_FLAGS.sizeof()
        # owner is just after mango_group in the layout, and it's a PublicKey which is 32 bytes.
        owner_offset = mango_group_offset + 32
        filters = [
            MemcmpOpts(
                offset=mango_group_offset,
                bytes=encode_key(group.address)
            ),
            MemcmpOpts(
                offset=owner_offset,
                bytes=encode_key(owner)
            )
        ]

        response = context.client.get_program_accounts(
            context.program_id, memcmp_opts=filters, commitment=context.commitment, encoding="base64")
        margin_accounts = []
        for margin_account_data in response["result"]:
            address = PublicKey(margin_account_data["pubkey"])
            account = AccountInfo._from_response_values(margin_account_data["account"], address)
            margin_account = MarginAccount.parse(account, group)
            margin_account.load_open_orders_accounts(context, group)
            margin_accounts += [margin_account]
        return margin_accounts

    @classmethod
    def filter_out_unripe(cls, margin_accounts: typing.List["MarginAccount"], group: Group, prices: typing.List[TokenValue]) -> typing.List["MarginAccount"]:
        logger: logging.Logger = logging.getLogger(cls.__name__)

        ripe_accounts: typing.List[MarginAccount] = []
        for margin_account in margin_accounts:
            balance_sheet = margin_account.get_balance_sheet_totals(group, prices)
            if balance_sheet.collateral_ratio > 0:
                if balance_sheet.collateral_ratio <= group.init_coll_ratio:
                    ripe_accounts += [margin_account]
        logger.info(
            f"Of those {len(margin_accounts)}, {len(ripe_accounts)} have a collateral ratio greater than zero but less than the initial collateral ratio of: {group.init_coll_ratio}.")
        return ripe_accounts

    def load_open_orders_accounts(self, context: Context, group: Group) -> None:
        for index, oo in enumerate(self.open_orders):
            key = oo
            if key is not None:
                self.open_orders_accounts[index] = OpenOrders.load(
                    context, key, group.basket_tokens[index].token.decimals, group.shared_quote_token.token.decimals)

    def install_open_orders_accounts(self, group: Group, all_open_orders_by_address: typing.Dict[str, AccountInfo]) -> None:
        for index, oo in enumerate(self.open_orders):
            key = str(oo)
            if key in all_open_orders_by_address:
                open_orders_account_info = all_open_orders_by_address[key]
                open_orders = OpenOrders.parse(open_orders_account_info,
                                               group.basket_tokens[index].token.decimals,
                                               group.shared_quote_token.token.decimals)
                self.open_orders_accounts[index] = open_orders

    def get_intrinsic_balance_sheets(self, group: Group) -> typing.List[BalanceSheet]:
        settled_assets: typing.List[Decimal] = [Decimal(0)] * len(group.basket_tokens)
        liabilities: typing.List[Decimal] = [Decimal(0)] * len(group.basket_tokens)
        for index, token in enumerate(group.basket_tokens):
            settled_assets[index] = self.deposits[index].value
            liabilities[index] = self.borrows[index].value

        unsettled_assets: typing.List[Decimal] = [Decimal(0)] * len(group.basket_tokens)
        for index, open_orders_account in enumerate(self.open_orders_accounts):
            if open_orders_account is not None:
                unsettled_assets[index] += open_orders_account.base_token_total
                unsettled_assets[-1] += open_orders_account.quote_token_total + \
                    open_orders_account.referrer_rebate_accrued

        balance_sheets: typing.List[BalanceSheet] = []
        for index, token in enumerate(group.basket_tokens):
            balance_sheets += [BalanceSheet(token.token, liabilities[index],
                                            settled_assets[index], unsettled_assets[index])]

        return balance_sheets

    def get_priced_balance_sheets(self, group: Group, prices: typing.List[TokenValue]) -> typing.List[BalanceSheet]:
        priced: typing.List[BalanceSheet] = []
        balance_sheets = self.get_intrinsic_balance_sheets(group)
        for balance_sheet in balance_sheets:
            price = TokenValue.find_by_token(prices, balance_sheet.token)
            liabilities = balance_sheet.liabilities * price.value
            settled_assets = balance_sheet.settled_assets * price.value
            unsettled_assets = balance_sheet.unsettled_assets * price.value
            priced += [BalanceSheet(
                price.token,
                price.token.round(liabilities),
                price.token.round(settled_assets),
                price.token.round(unsettled_assets)
            )]

        return priced

    def get_balance_sheet_totals(self, group: Group, prices: typing.List[TokenValue]) -> BalanceSheet:
        liabilities = Decimal(0)
        settled_assets = Decimal(0)
        unsettled_assets = Decimal(0)

        balance_sheets = self.get_priced_balance_sheets(group, prices)
        for balance_sheet in balance_sheets:
            if balance_sheet is not None:
                liabilities += balance_sheet.liabilities
                settled_assets += balance_sheet.settled_assets
                unsettled_assets += balance_sheet.unsettled_assets

        # A BalanceSheet must have a token - it's a pain to make it a typing.Optional[Token].
        # So in this one case, we produce a 'fake' token whose symbol is a summary of all token
        # symbols that went into it.
        #
        # If this becomes more painful than typing.Optional[Token], we can go with making
        # Token optional.
        summary_name = "-".join([bal.token.name for bal in balance_sheets])
        summary_token = Token(summary_name, f"{summary_name} Summary", SYSTEM_PROGRAM_ADDRESS, Decimal(0))
        return BalanceSheet(summary_token, liabilities, settled_assets, unsettled_assets)

    def get_intrinsic_balances(self, group: Group) -> typing.List[TokenValue]:
        balance_sheets = self.get_intrinsic_balance_sheets(group)
        balances: typing.List[TokenValue] = []
        for index, balance_sheet in enumerate(balance_sheets):
            if balance_sheet.token is None:
                raise Exception(f"Intrinsic balance sheet with index [{index}] has no token.")
            balances += [TokenValue(balance_sheet.token, balance_sheet.value)]

        return balances

    # The old way of fetching ripe margin accounts was to fetch them all then inspect them to see
    # if they were ripe. That was a big performance problem - fetching all groups was quite a penalty.
    #
    # This is still how it's done in load_ripe_v1().
    #
    # The newer mechanism is to look for the has_borrows flag in the ManrginAccount. That should
    # mean fewer MarginAccounts need to be fetched.
    #
    # This newer method is implemented in load_ripe_v2()
    @staticmethod
    def load_ripe(context: Context, group: Group) -> typing.List["MarginAccount"]:
        if group.version == Version.V1:
            return MarginAccount._load_ripe_v1(context, group)
        else:
            return MarginAccount._load_ripe_v2(context, group)

    @classmethod
    def _load_ripe_v1(cls, context: Context, group: Group) -> typing.List["MarginAccount"]:
        started_at = time.time()
        logger: logging.Logger = logging.getLogger(cls.__name__)

        margin_accounts = MarginAccount.load_all_for_group_with_open_orders(context, context.program_id, group)
        logger.info(f"Fetched {len(margin_accounts)} V1 margin accounts to process.")

        prices = group.fetch_token_prices(context)
        ripe_accounts = MarginAccount.filter_out_unripe(margin_accounts, group, prices)

        time_taken = time.time() - started_at
        logger.info(f"Loading ripe 🥭 accounts complete. Time taken: {time_taken:.2f} seconds.")
        return ripe_accounts

    @classmethod
    def _load_ripe_v2(cls, context: Context, group: Group) -> typing.List["MarginAccount"]:
        started_at = time.time()
        logger: logging.Logger = logging.getLogger(cls.__name__)

        filters = [
            # 'has_borrows' offset is: 8 + 32 + 32 + (5 * 16) + (5 * 16) + (4 * 32) + 1
            # = 361
            MemcmpOpts(
                offset=361,
                bytes=encode_int(1)
            ),
            MemcmpOpts(
                offset=layouts.MANGO_ACCOUNT_FLAGS.sizeof(),  # mango_group is just after the MangoAccountFlags, which is the first entry
                bytes=encode_key(group.address)
            )
        ]

        data_size = layouts.MARGIN_ACCOUNT_V2.sizeof()
        response = context.client.get_program_accounts(
            context.program_id, data_size=data_size, memcmp_opts=filters, commitment=context.commitment, encoding="base64")
        result = context.unwrap_or_raise_exception(response)
        margin_accounts = []
        open_orders_addresses = []
        for margin_account_data in result:
            address = PublicKey(margin_account_data["pubkey"])
            account = AccountInfo._from_response_values(margin_account_data["account"], address)
            margin_account = MarginAccount.parse(account, group)
            open_orders_addresses += margin_account.open_orders
            margin_accounts += [margin_account]

        logger.info(f"Fetched {len(margin_accounts)} V2 margin accounts to process.")

        # It looks like this will be more efficient - just specify only the addresses we
        # need, and install them.
        #
        # Unfortunately there's a limit of 100 for the getMultipleAccounts() RPC call,
        # and doing it repeatedly requires some pauses because of rate limits.
        #
        # It's quicker (so far) to bring back every openorders account for the group.
        #
        # open_orders_addresses = [oo for oo in open_orders_addresses if oo is not None]

        # open_orders_account_infos = AccountInfo.load_multiple(self.context, open_orders_addresses)
        # open_orders_account_infos_by_address = {key: value for key, value in [(str(account_info.address), account_info) for account_info in open_orders_account_infos]}

        # for margin_account in margin_accounts:
        #     margin_account.install_open_orders_accounts(self, open_orders_account_infos_by_address)

        # This just fetches every openorder account for the group.
        open_orders = OpenOrders.load_raw_open_orders_account_infos(context, group)
        logger.info(f"Fetched {len(open_orders)} openorders accounts.")
        for margin_account in margin_accounts:
            margin_account.install_open_orders_accounts(group, open_orders)

        prices = group.fetch_token_prices(context)
        ripe_accounts = MarginAccount.filter_out_unripe(margin_accounts, group, prices)

        time_taken = time.time() - started_at
        logger.info(f"Loading ripe 🥭 accounts complete. Time taken: {time_taken:.2f} seconds.")
        return ripe_accounts

    def __str__(self) -> str:
        deposits = "\n        ".join([f"{item}" for item in self.deposits])
        borrows = "\n        ".join([f"{item:}" for item in self.borrows])
        if all(oo is None for oo in self.open_orders_accounts):
            open_orders = f"{self.open_orders}"
        else:
            open_orders_unindented = f"{self.open_orders_accounts}"
            open_orders = open_orders_unindented.replace("\n", "\n    ")
        return f"""« MarginAccount: {self.address}
    Flags: {self.account_flags}
    Has Borrows: {self.has_borrows}
    Owner: {self.owner}
    Mango Group: {self.mango_group}
    Deposits:
        {deposits}
    Borrows:
        {borrows}
    Mango Open Orders: {open_orders}
»"""
