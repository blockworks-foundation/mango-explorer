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
from .openorders import OpenOrders
from .orders import Side
from .perpaccount import PerpAccount
from .perpopenorders import PerpOpenOrders
from .placedorder import PlacedOrder
from .token import Token
from .tokeninfo import TokenInfo
from .tokenvalue import TokenValue
from .version import Version


# # 🥭 AccountBasketToken class
#
# `AccountBasketToken` gathers basket items together instead of separate arrays.
#
class AccountBasketToken:
    def __init__(self, token_info: TokenInfo, deposit: TokenValue, borrow: TokenValue):
        self.token_info: TokenInfo = token_info
        self.deposit: TokenValue = deposit
        self.borrow: TokenValue = borrow

    @property
    def net_value(self) -> TokenValue:
        return self.deposit - self.borrow

    def __str__(self) -> str:
        return f"""« 𝙰𝚌𝚌𝚘𝚞𝚗𝚝𝙱𝚊𝚜𝚔𝚎𝚝𝚃𝚘𝚔𝚎𝚗 {self.token_info.token.symbol}
    Net Value:     {self.net_value}
        Deposited: {self.deposit}
        Borrowed:  {self.borrow}
»"""

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 AccountBasketBaseToken class
#
# `AccountBasketBaseToken` is a more specialised `AccountBasketToken` for all the base tokens in the
# account.
#
class AccountBasketBaseToken(AccountBasketToken):
    def __init__(self, token_info: TokenInfo, quote_token_info: TokenInfo, deposit: TokenValue, borrow: TokenValue, spot_open_orders: typing.Optional[PublicKey], perp_account: typing.Optional[PerpAccount]):
        super().__init__(token_info, deposit, borrow)
        self.quote_token_info: TokenInfo = quote_token_info
        self.spot_open_orders: typing.Optional[PublicKey] = spot_open_orders
        self.perp_account: typing.Optional[PerpAccount] = perp_account

    def __str__(self) -> str:
        perp_account: str = "None"
        if self.perp_account is not None:
            perp_account = f"{self.perp_account}".replace("\n", "\n        ")
        return f"""« 𝙰𝚌𝚌𝚘𝚞𝚗𝚝𝙱𝚊𝚜𝚔𝚎𝚝𝙱𝚊𝚜𝚎𝚃𝚘𝚔𝚎𝚗 {self.token_info.token.symbol}
    Net Value:     {self.net_value}
        Deposited: {self.deposit}
        Borrowed:  {self.borrow}
    Spot OpenOrders: {self.spot_open_orders or "None"}
    Perp Account:
        {perp_account}
»"""

    def __repr__(self) -> str:
        return f"{self}"


TMappedAccountBasketValue = typing.TypeVar("TMappedAccountBasketValue")


# # 🥭 Account class
#
# `Account` holds information about the account for a particular user/wallet for a particualr `Group`.
#
class Account(AddressableAccount):
    def __init__(self, account_info: AccountInfo, version: Version,
                 meta_data: Metadata, group_name: str, group_address: PublicKey, owner: PublicKey,
                 info: str, shared_quote_token: AccountBasketToken,
                 in_margin_basket: typing.Sequence[bool],
                 basket_indices: typing.Sequence[bool],
                 basket: typing.Sequence[AccountBasketBaseToken],
                 msrm_amount: Decimal, being_liquidated: bool, is_bankrupt: bool):
        super().__init__(account_info)
        self.version: Version = version

        self.meta_data: Metadata = meta_data
        self.group_name: str = group_name
        self.group_address: PublicKey = group_address
        self.owner: PublicKey = owner
        self.info: str = info
        self.shared_quote_token: AccountBasketToken = shared_quote_token
        self.in_margin_basket: typing.Sequence[bool] = in_margin_basket
        self.basket_indices: typing.Sequence[bool] = basket_indices
        self.basket: typing.Sequence[AccountBasketBaseToken] = basket
        self.msrm_amount: Decimal = msrm_amount
        self.being_liquidated: bool = being_liquidated
        self.is_bankrupt: bool = is_bankrupt

    @staticmethod
    def from_layout(layout: typing.Any, account_info: AccountInfo, version: Version, group: Group) -> "Account":
        meta_data = Metadata.from_layout(layout.meta_data)
        owner: PublicKey = layout.owner
        info: str = layout.info
        mngo_token_info = TokenInfo.find_by_symbol(group.tokens, "MNGO")
        in_margin_basket: typing.Sequence[bool] = list([bool(in_basket) for in_basket in layout.in_margin_basket])
        active_in_basket: typing.List[bool] = []
        basket: typing.List[AccountBasketBaseToken] = []
        placed_orders_all_markets: typing.List[typing.List[PlacedOrder]] = [[] for _ in range(len(group.tokens) - 1)]
        for index, order_market in enumerate(layout.order_market):
            if order_market != 0xFF:
                side = Side.from_value(layout.order_side[index])
                id = layout.order_ids[index]
                client_id = layout.client_order_ids[index]
                placed_order = PlacedOrder(id, client_id, side)
                placed_orders_all_markets[int(order_market)] += [placed_order]

        quote_token_info: typing.Optional[TokenInfo] = group.tokens[-1]
        if quote_token_info is None:
            raise Exception(f"Could not determine quote token in group {group.address}")

        for index, token_info in enumerate(group.tokens[:-1]):
            if token_info:
                intrinsic_deposit = token_info.root_bank.deposit_index * layout.deposits[index]
                deposit = TokenValue(token_info.token, token_info.token.shift_to_decimals(intrinsic_deposit))
                intrinsic_borrow = token_info.root_bank.borrow_index * layout.borrows[index]
                borrow = TokenValue(token_info.token, token_info.token.shift_to_decimals(intrinsic_borrow))
                perp_open_orders = PerpOpenOrders(placed_orders_all_markets[index])
                group_basket_market = group.markets[index]
                if group_basket_market is None:
                    raise Exception(f"Could not find group basket market at index {index}.")
                perp_account = PerpAccount.from_layout(
                    layout.perp_accounts[index],
                    token_info.token,
                    quote_token_info.token,
                    perp_open_orders,
                    group_basket_market.perp_lot_size_converter,
                    mngo_token_info.token)
                spot_open_orders = layout.spot_open_orders[index]
                basket_item: AccountBasketBaseToken = AccountBasketBaseToken(
                    token_info, quote_token_info, deposit, borrow, spot_open_orders, perp_account)
                basket += [basket_item]
                active_in_basket += [True]
            else:
                active_in_basket += [False]

        intrinsic_quote_deposit = quote_token_info.root_bank.deposit_index * layout.deposits[-1]
        quote_deposit = TokenValue(quote_token_info.token,
                                   quote_token_info.token.shift_to_decimals(intrinsic_quote_deposit))
        intrinsic_quote_borrow = quote_token_info.root_bank.borrow_index * layout.borrows[-1]
        quote_borrow = TokenValue(quote_token_info.token,
                                  quote_token_info.token.shift_to_decimals(intrinsic_quote_borrow))
        quote: AccountBasketToken = AccountBasketToken(quote_token_info, quote_deposit, quote_borrow)

        msrm_amount: Decimal = layout.msrm_amount
        being_liquidated: bool = bool(layout.being_liquidated)
        is_bankrupt: bool = bool(layout.is_bankrupt)

        return Account(account_info, version, meta_data, group.name, group.address, owner, info, quote, in_margin_basket, active_in_basket, basket, msrm_amount, being_liquidated, is_bankrupt)

    @staticmethod
    def parse(account_info: AccountInfo, group: Group) -> "Account":
        data = account_info.data
        if len(data) != layouts.MANGO_ACCOUNT.sizeof():
            raise Exception(
                f"Account data length ({len(data)}) does not match expected size ({layouts.MANGO_ACCOUNT.sizeof()})")

        layout = layouts.MANGO_ACCOUNT.parse(data)
        return Account.from_layout(layout, account_info, Version.V3, group)

    @staticmethod
    def load(context: Context, address: PublicKey, group: Group) -> "Account":
        account_info = AccountInfo.load(context, address)
        if account_info is None:
            raise Exception(f"Account account not found at address '{address}'")
        return Account.parse(account_info, group)

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

        results = context.client.get_program_accounts(context.mango_program_address, memcmp_opts=filters)
        accounts = []
        for account_data in results:
            address = PublicKey(account_data["pubkey"])
            account_info = AccountInfo._from_response_values(account_data["account"], address)
            account = Account.parse(account_info, group)
            accounts += [account]
        return accounts

    @staticmethod
    def load_for_owner_by_address(context: Context, owner: PublicKey, group: Group, account_address: typing.Optional[PublicKey]) -> "Account":
        if account_address is not None:
            return Account.load(context, account_address, group)

        accounts: typing.Sequence[Account] = Account.load_all_for_owner(context, owner, group)
        if len(accounts) > 1:
            raise Exception(f"More than 1 Mango account for owner '{owner}' and which to choose not specified.")

        return accounts[0]

    @staticmethod
    def _map_sequence_to_basket_indices(items: typing.Sequence[AccountBasketBaseToken], in_basket: typing.Sequence[bool], selector: typing.Callable[[typing.Any], TMappedAccountBasketValue]) -> typing.Sequence[typing.Optional[TMappedAccountBasketValue]]:
        mapped_items: typing.List[typing.Optional[TMappedAccountBasketValue]] = []
        basket_counter = 0
        for available in in_basket:
            if available:
                mapped_items += [selector(items[basket_counter])]
                basket_counter += 1
            else:
                mapped_items += [None]

        return mapped_items

    @property
    def basket_tokens(self) -> typing.Sequence[typing.Optional[AccountBasketToken]]:
        return [
            *Account._map_sequence_to_basket_indices(self.basket, self.basket_indices, lambda item: item),
            self.shared_quote_token
        ]

    @property
    def deposits(self) -> typing.Sequence[typing.Optional[TokenValue]]:
        return list(map(lambda basket_token: basket_token.deposit if basket_token else None, self.basket_tokens))

    @property
    def borrows(self) -> typing.Sequence[typing.Optional[TokenValue]]:
        return list(map(lambda basket_token: basket_token.borrow if basket_token else None, self.basket_tokens))

    @property
    def net_assets(self) -> typing.Sequence[typing.Optional[TokenValue]]:
        return list(map(lambda basket_token: basket_token.net_value if basket_token else None, self.basket_tokens))

    @property
    def spot_open_orders(self) -> typing.Sequence[typing.Optional[PublicKey]]:
        return Account._map_sequence_to_basket_indices(self.basket, self.basket_indices, lambda item: item.spot_open_orders)

    @property
    def perp_accounts(self) -> typing.Sequence[typing.Optional[PerpAccount]]:
        return Account._map_sequence_to_basket_indices(self.basket, self.basket_indices, lambda item: item.perp_account)

    def find_basket_token(self, token: Token) -> AccountBasketBaseToken:
        for bt in self.basket:
            if bt.token_info.token == token:
                return bt

        raise Exception(f"Could not find token {token} in basket in group {self.address}")

    def load_all_spot_open_orders(self, context: Context) -> typing.Dict[str, OpenOrders]:
        spot_open_orders_addresses = list(
            [basket_token.spot_open_orders for basket_token in self.basket if basket_token.spot_open_orders is not None])
        spot_open_orders_account_infos = AccountInfo.load_multiple(context, spot_open_orders_addresses)
        spot_open_orders_account_infos_by_address = {
            str(account_info.address): account_info for account_info in spot_open_orders_account_infos}
        spot_open_orders: typing.Dict[str, OpenOrders] = {}
        for basket_token in self.basket:
            if basket_token.spot_open_orders is not None:
                account_info = spot_open_orders_account_infos_by_address[str(basket_token.spot_open_orders)]
                oo = OpenOrders.parse(account_info, basket_token.token_info.token.decimals,
                                      self.shared_quote_token.token_info.decimals)
                spot_open_orders[str(basket_token.spot_open_orders)] = oo
        return spot_open_orders

    def update_spot_open_orders_for_market(self, spot_market_index: int, spot_open_orders: PublicKey) -> None:
        indexable_basket: typing.Sequence[typing.Optional[AccountBasketBaseToken]] = Account._map_sequence_to_basket_indices(
            self.basket, self.basket_indices, lambda item: item)
        item_to_update = indexable_basket[spot_market_index]
        if item_to_update is None:
            raise Exception(f"Could not find AccountBasketItem in Account {self.address} at index {spot_market_index}.")
        item_to_update.spot_open_orders = spot_open_orders

    def __str__(self) -> str:
        info = f"'{self.info}'" if self.info else "(𝑢𝑛-𝑛𝑎𝑚𝑒𝑑)"
        shared_quote_token: str = f"{self.shared_quote_token}".replace("\n", "\n        ")
        basket_count = len(self.basket)
        basket = "\n        ".join([f"{item}".replace("\n", "\n        ") for item in self.basket])

        tokens_in_basket: typing.Sequence[typing.Optional[Token]] = Account._map_sequence_to_basket_indices(
            self.basket, self.basket_indices, lambda item: item.token_info.token)
        symbols_in_basket = list([tok.symbol for tok in tokens_in_basket if tok is not None])
        in_margin_basket = ", ".join(symbols_in_basket) or "None"
        return f"""« 𝙰𝚌𝚌𝚘𝚞𝚗𝚝 {info}, {self.version} [{self.address}]
    {self.meta_data}
    Owner: {self.owner}
    Group: « 𝙶𝚛𝚘𝚞𝚙 '{self.group_name}' [{self.group_address}] »
    MSRM: {self.msrm_amount}
    Bankrupt? {self.is_bankrupt}
    Being Liquidated? {self.being_liquidated}
    Shared Quote Token:
        {shared_quote_token}
    In Basket: {in_margin_basket}
    Basket [{basket_count} in basket]:
        {basket}
»"""

    def __repr__(self) -> str:
        return f"{self}"
