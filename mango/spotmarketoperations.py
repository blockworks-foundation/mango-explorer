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


import itertools
import typing

from decimal import Decimal
from pyserum.market import Market
from pyserum.market.orderbook import OrderBook as SerumOrderBook
from pyserum.market.types import Order as SerumOrder
from solana.account import Account as SolanaAccount
from solana.publickey import PublicKey
from solana.transaction import Transaction

from .account import Account
from .accountinfo import AccountInfo
from .context import Context
from .group import Group
from .instructions import build_compound_spot_place_order_instructions, build_cancel_spot_order_instructions
from .marketoperations import MarketOperations
from .orders import Order, OrderType, Side
from .spotmarket import SpotMarket
from .tokenaccount import TokenAccount
from .wallet import Wallet


# # 🥭 SpotMarketOperations class
#
# This class puts trades on the Serum orderbook. It doesn't do anything complicated.
#

class SpotMarketOperations(MarketOperations):
    def __init__(self, context: Context, wallet: Wallet, group: Group, account: Account, spot_market: SpotMarket, reporter: typing.Callable[[str], None] = None):
        super().__init__()
        self.context: Context = context
        self.wallet: Wallet = wallet
        self.group: Group = group
        self.account: Account = account
        self.spot_market: SpotMarket = spot_market
        self.market: Market = Market.load(context.client, spot_market.address, context.dex_program_id)
        self._serum_fee_discount_token_address: typing.Optional[PublicKey] = None
        self._serum_fee_discount_token_address_loaded: bool = False

        market_index: int = -1
        for index, spot in enumerate(self.group.spot_markets):
            if spot is not None and spot.address == self.spot_market.address:
                market_index = index
        if market_index == -1:
            raise Exception(f"Could not find spot market {self.spot_market.address} in group {self.group.address}")

        self.group_market_index: int = market_index

        def report(text):
            self.logger.info(text)
            reporter(text)

        def just_log(text):
            self.logger.info(text)

        if reporter is not None:
            self.reporter = report
        else:
            self.reporter = just_log

    @property
    def serum_fee_discount_token_address(self) -> typing.Optional[PublicKey]:
        if self._serum_fee_discount_token_address_loaded:
            return self._serum_fee_discount_token_address

        # SRM is always the token Serum uses for fee discounts
        token = self.context.token_lookup.find_by_symbol("SRM")
        if token is None:
            self._serum_fee_discount_token_address_loaded = True
            self._serum_fee_discount_token_address = None
            return self._serum_fee_discount_token_address

        fee_discount_token_account = TokenAccount.fetch_largest_for_owner_and_token(
            self.context, self.wallet.address, token)
        if fee_discount_token_account is not None:
            self._serum_fee_discount_token_address = fee_discount_token_account.address

        self._serum_fee_discount_token_address_loaded = True
        return self._serum_fee_discount_token_address

    def cancel_order(self, order: Order) -> str:
        report = f"Cancelling order {order.id} on market {self.spot_market.symbol}."
        self.logger.info(report)
        self.reporter(report)

        open_orders = self.account.spot_open_orders[self.group_market_index]

        signers: typing.Sequence[SolanaAccount] = [self.wallet.account]
        transaction = Transaction()
        cancel_instructions = build_cancel_spot_order_instructions(
            self.context, self.wallet, self.group, self.account, self.market, order, open_orders)
        transaction.instructions.extend(cancel_instructions)
        response = self.context.client.send_transaction(transaction, *signers, opts=self.context.transaction_options)
        return self.context.unwrap_transaction_id_or_raise_exception(response)

    def place_order(self, side: Side, order_type: OrderType, price: Decimal, size: Decimal) -> Order:
        payer_token = self.spot_market.quote if side == Side.BUY else self.spot_market.base
        payer_token_account = TokenAccount.fetch_largest_for_owner_and_token(
            self.context, self.wallet.address, payer_token)
        if payer_token_account is None:
            raise Exception(f"Could not find a source token account for token {payer_token}.")

        open_orders = self.account.spot_open_orders[self.group_market_index]
        client_order_id = self.context.random_client_id()
        report = f"Placing {order_type} {side} order for size {size} at price {price} on market {self.spot_market.symbol} using client ID {client_order_id}."
        self.logger.info(report)
        self.reporter(report)

        signers: typing.Sequence[SolanaAccount] = [self.wallet.account]
        transaction = Transaction()
        place_instructions = build_compound_spot_place_order_instructions(
            self.context, self.wallet, self.group, self.account, self.market, payer_token_account.address,
            open_orders, order_type, side, price, size, client_order_id, self.serum_fee_discount_token_address)

        transaction.instructions.extend(place_instructions)
        response = self.context.client.send_transaction(transaction, *signers, opts=self.context.transaction_options)
        self.context.unwrap_transaction_id_or_raise_exception(response)

        return Order(id=0, side=side, price=price, size=size, client_id=client_order_id, owner=self.account.address)

    def _load_serum_orders(self) -> typing.Sequence[SerumOrder]:
        [bids_info, asks_info] = AccountInfo.load_multiple(
            self.context, [self.market.state.bids(), self.market.state.asks()])
        bids_orderbook = SerumOrderBook.from_bytes(self.market.state, bids_info.data)
        asks_orderbook = SerumOrderBook.from_bytes(self.market.state, asks_info.data)

        return list(itertools.chain(bids_orderbook.orders(), asks_orderbook.orders()))

    def load_orders(self) -> typing.Sequence[Order]:
        all_orders = self._load_serum_orders()
        orders: typing.List[Order] = []
        for serum_order in all_orders:
            orders += [Order.from_serum_order(serum_order)]

        return orders

    def load_my_orders(self) -> typing.Sequence[Order]:
        open_orders_account = self.account.spot_open_orders[self.group_market_index]
        if not open_orders_account:
            return []

        all_orders = self._load_serum_orders()
        serum_orders = [o for o in all_orders if o.open_order_address == open_orders_account]
        orders: typing.List[Order] = []
        for serum_order in serum_orders:
            orders += [Order.from_serum_order(serum_order)]

        return orders

    def __str__(self) -> str:
        return f"""« 𝚂𝚙𝚘𝚝𝙼𝚊𝚛𝚔𝚎𝚝𝙾𝚙𝚎𝚛𝚊𝚝𝚒𝚘𝚗𝚜 [{self.spot_market.symbol}] »"""
