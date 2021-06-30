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


import pyserum.enums
import typing

from decimal import Decimal
from pyserum.market import Market
from solana.rpc.types import TxOpts

from .context import Context
from .marketoperations import MarketOperations
from .openorders import OpenOrders
from .orders import Order, OrderType, Side
from .serummarket import SerumMarket
from .tokenaccount import TokenAccount
from .wallet import Wallet


# # 🥭 SerumMarketOperations class
#
# This class puts trades on the Serum orderbook. It doesn't do anything complicated.
#

class SerumMarketOperations(MarketOperations):
    def __init__(self, context: Context, wallet: Wallet, serum_market: SerumMarket, reporter: typing.Callable[[str], None] = None):
        super().__init__()
        self.context: Context = context
        self.wallet: Wallet = wallet
        self.serum_market: SerumMarket = serum_market
        self.market: Market = Market.load(context.client, serum_market.address, context.dex_program_id)
        all_open_orders = OpenOrders.load_for_market_and_owner(
            context, serum_market.address, wallet.address, context.dex_program_id, serum_market.base.decimals, serum_market.quote.decimals)
        if len(all_open_orders) == 0:
            raise Exception(f"No OpenOrders account available for market {serum_market}.")
        self.open_orders = all_open_orders[0]

        def report(text):
            self.logger.info(text)
            reporter(text)

        def just_log(text):
            self.logger.info(text)

        if reporter is not None:
            self.reporter = report
        else:
            self.reporter = just_log

    def cancel_order(self, order: Order) -> str:
        self.reporter(
            f"Cancelling order {order.id} in openorders {self.open_orders.address} on market {self.serum_market.symbol}.")
        try:
            response = self.market.cancel_order_by_client_id(
                self.wallet.account, self.open_orders.address, order.id,
                TxOpts(preflight_commitment=self.context.commitment))
            return self.context.unwrap_transaction_id_or_raise_exception(response)
        except Exception as exception:
            self.logger.warning(f"Failed to cancel order {order.id} - continuing. {exception}")
            return ""

    def place_order(self, side: Side, order_type: OrderType, price: Decimal, size: Decimal) -> Order:
        client_id: int = self.context.random_client_id()
        report: str = f"Placing {order_type} {side} order for size {size} at price {price} on market {self.serum_market.symbol} with ID {client_id}."
        self.logger.info(report)
        self.reporter(report)
        serum_order_type = pyserum.enums.OrderType.POST_ONLY if order_type == OrderType.POST_ONLY else pyserum.enums.OrderType.IOC if order_type == OrderType.IOC else pyserum.enums.OrderType.LIMIT
        serum_side = pyserum.enums.Side.BUY if side == Side.BUY else pyserum.enums.Side.SELL
        payer_token = self.serum_market.quote if side == Side.BUY else self.serum_market.base
        token_account = TokenAccount.fetch_largest_for_owner_and_token(self.context, self.wallet.address, payer_token)
        if token_account is None:
            raise Exception(f"Could not find payer token account for token {payer_token.symbol}.")

        response = self.market.place_order(token_account.address, self.wallet.account,
                                           serum_order_type, serum_side, float(price), float(size),
                                           client_id, TxOpts(preflight_commitment=self.context.commitment))
        self.context.unwrap_or_raise_exception(response)
        return Order(id=0, side=side, price=price, size=size, client_id=client_id, owner=self.open_orders.address)

    def load_orders(self) -> typing.Sequence[Order]:
        asks = self.market.load_asks()
        orders: typing.List[Order] = []
        for serum_order in asks:
            orders += [Order.from_serum_order(serum_order)]

        bids = self.market.load_bids()
        for serum_order in bids:
            orders += [Order.from_serum_order(serum_order)]

        return orders

    def load_my_orders(self) -> typing.Sequence[Order]:
        serum_orders = self.market.load_orders_for_owner(self.wallet.address)
        orders: typing.List[Order] = []
        for serum_order in serum_orders:
            orders += [Order.from_serum_order(serum_order)]

        return orders

    def __str__(self) -> str:
        return f"""« 𝚂𝚎𝚛𝚞𝚖𝙼𝚊𝚛𝚔𝚎𝚝𝙾𝚙𝚎𝚛𝚊𝚝𝚒𝚘𝚗𝚜 [{self.serum_market.symbol}] »"""
