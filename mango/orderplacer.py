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


import abc
import enum
import logging

import pyserum.enums
import typing

from decimal import Decimal
from pyserum.market import Market
from solana.rpc.types import TxOpts

from .context import Context
from .openorders import OpenOrders
from .spotmarket import SpotMarket
from .tokenaccount import TokenAccount
from .wallet import Wallet


# # 🥭 OrderPlacer
#
# This file deals with placing orders. We want the interface to be simple and basic:
# ```
# order_placer.cancel_order(context, market)
# order_placer.place_order(context, market, side, order_type, price, size)
# ```
# This requires the `OrderPlacer` already know a bit about the market it is placing the
# order on, and the code in the `OrderPlacer` be specialised for that market platform.
#


class Side(enum.Enum):
    BUY = enum.auto()
    SELL = enum.auto()

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"{self}"


class OrderType(enum.Enum):
    LIMIT = enum.auto()
    IOC = enum.auto()
    POST_ONLY = enum.auto()

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"{self}"


class Order(typing.NamedTuple):
    id: int
    side: Side
    price: Decimal
    size: Decimal


# # 🥭 OrderPlacer class
#
# This abstracts the process of placing orders, providing a base class for specialised operations.
#
# It's abstracted because we may want to have different approaches to placing these
# orders - do we want to run them against the Serum orderbook? Do we want to run them against
# Mango groups?
#
# Whichever choice is made, the calling code shouldn't have to care. It should be able to
# use its `OrderPlacer` class as simply as:
# ```
# order_placer.place_order(context, side, order_type, price, size)
# ```
#


class OrderPlacer(metaclass=abc.ABCMeta):
    def __init__(self):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)

    @abc.abstractmethod
    def cancel_order(self, order: Order) -> None:
        raise NotImplementedError("OrderPlacer.cancel_order() is not implemented on the base type.")

    @abc.abstractmethod
    def place_order(self, side: Side, order_type: OrderType, price: Decimal, size: Decimal) -> Order:
        raise NotImplementedError("OrderPlacer.place_order() is not implemented on the base type.")

    @abc.abstractmethod
    def load_my_orders(self) -> typing.List[Order]:
        raise NotImplementedError("OrderPlacer.load_my_orders() is not implemented on the base type.")

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 NullOrderPlacer class
#
# A null, no-op, dry-run trade executor that can be plugged in anywhere a `OrderPlacer`
# is expected, but which will not actually trade.
#

class NullOrderPlacer(OrderPlacer):
    def __init__(self, market_name: str, reporter: typing.Callable[[str], None] = None):
        super().__init__()
        self.market_name: str = market_name
        self.reporter = reporter or (lambda _: None)

    def cancel_order(self, order: Order) -> None:
        report = f"Cancelling order on market {self.market_name}."
        self.logger.info(report)
        self.reporter(report)

    def place_order(self, side: Side, order_type: OrderType, price: Decimal, size: Decimal) -> Order:
        report = f"Placing {order_type} {side} order for size {size} at price {price} on market {self.market_name}."
        self.logger.info(report)
        self.reporter(report)
        return Order()

    def load_my_orders(self) -> typing.List[Order]:
        return []

    def __str__(self) -> str:
        return f"""« NullOrderPlacer [{self.market_name}] »"""


# # 🥭 SerumOrderPlacer class
#
# This class puts trades on the Serum orderbook. It doesn't do anything complicated.
#

class SerumOrderPlacer(OrderPlacer):
    def __init__(self, context: Context, wallet: Wallet, spot_market: SpotMarket, reporter: typing.Callable[[str], None] = None):
        super().__init__()
        self.context: Context = context
        self.wallet: Wallet = wallet
        self.spot_market: SpotMarket = spot_market
        self.market: Market = Market.load(context.client, spot_market.address, context.dex_program_id)
        all_open_orders = OpenOrders.load_for_market_and_owner(
            context, spot_market.address, wallet.address, context.dex_program_id, spot_market.base.decimals, spot_market.quote.decimals)
        if len(all_open_orders) == 0:
            raise Exception(f"No OpenOrders account available for market {spot_market}.")
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

    def cancel_order(self, order: Order) -> None:
        self.reporter(
            f"Cancelling order {order.id} in openorders {self.open_orders.address} on market {self.spot_market.symbol}.")
        try:
            response = self.market.cancel_order_by_client_id(
                self.wallet.account, self.open_orders.address, order.id,
                TxOpts(preflight_commitment=self.context.commitment))
            self.context.unwrap_or_raise_exception(response)
        except Exception as exception:
            self.logger.warning(f"Failed to cancel order {order.id} - continuing. {exception}")

    def place_order(self, side: Side, order_type: OrderType, price: Decimal, size: Decimal) -> Order:
        client_id: int = self.context.random_client_id()
        report: str = f"Placing {order_type} {side} order for size {size} at price {price} on market {self.spot_market.symbol} with ID {client_id}."
        self.logger.info(report)
        self.reporter(report)
        serum_order_type = pyserum.enums.OrderType.POST_ONLY if order_type == OrderType.POST_ONLY else pyserum.enums.OrderType.IOC if order_type == OrderType.IOC else pyserum.enums.OrderType.LIMIT
        serum_side = pyserum.enums.Side.BUY if side == Side.BUY else pyserum.enums.Side.SELL
        payer_token = self.spot_market.quote if side == Side.BUY else self.spot_market.base
        token_account = TokenAccount.fetch_largest_for_owner_and_token(self.context, self.wallet.address, payer_token)
        if token_account is None:
            raise Exception(f"Could not find payer token account for token {payer_token.symbol}.")

        response = self.market.place_order(token_account.address, self.wallet.account,
                                           serum_order_type, serum_side, float(price), float(size),
                                           client_id, TxOpts(preflight_commitment=self.context.commitment))
        self.context.unwrap_or_raise_exception(response)
        return Order(id=client_id, side=side, price=price, size=size)

    def load_my_orders(self) -> typing.List[Order]:
        serum_orders = self.market.load_orders_for_owner(self.wallet.address)
        orders: typing.List[Order] = []
        for serum_order in serum_orders:
            price = Decimal(serum_order.info.price)
            size = Decimal(serum_order.info.size)
            side = Side.BUY if serum_order.side == pyserum.enums.Side.BUY else Side.SELL
            order = Order(id=serum_order.client_id, side=side, price=price, size=size)
            orders += [order]

        return orders

    def __str__(self) -> str:
        return f"""« SerumOrderPlacer [{self.spot_market.symbol}] »"""
