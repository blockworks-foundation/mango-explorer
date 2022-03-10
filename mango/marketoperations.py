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
import logging
import typing

from datetime import datetime
from decimal import Decimal
from solana.publickey import PublicKey

from .combinableinstructions import CombinableInstructions
from .constants import SYSTEM_PROGRAM_ADDRESS
from .datetimes import utc_now
from .loadedmarket import LoadedMarket
from .lotsizeconverter import NullLotSizeConverter
from .markets import InventorySource
from .orders import Order, OrderBook, OrderType, Side


# # 🥭 MarketOperations
#
# This file deals with placing orders. We want the interface to be simple and basic:
# ```
# market_operations.cancel_order(old_order)
# market_operations.place_order(new_order)
# ```
# This requires the `MarketOperations` already know a bit about the market it is placing the
# order on, and the code in the `MarketOperations` be specialised for that market platform.
#


# # 🥭 MarketInstructionBuilder class
#
# This abstracts the process of buiding instructions for placing orders and cancelling orders.
#
# It's abstracted because we may want to have different implementations for different market types.
#
# Whichever choice is made, the calling code shouldn't have to care. It should be able to
# use its `MarketInstructionBuilder` class as simply as:
# ```
# instruction_builder.build_cancel_order_instructions(order)
# ```
#
# As a matter of policy for all InstructionBuidlers, construction and build_* methods should all work with
# existing data, requiring no fetches from Solana or other sources. All necessary data should all be loaded
# on initial setup in the `load()` method.
#
class MarketInstructionBuilder(metaclass=abc.ABCMeta):
    def __init__(self) -> None:
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.open_orders_address: typing.Optional[PublicKey] = None

    @abc.abstractmethod
    def build_cancel_order_instructions(
        self, order: Order, ok_if_missing: bool = False
    ) -> CombinableInstructions:
        raise NotImplementedError(
            "MarketInstructionBuilder.build_cancel_order_instructions() is not implemented on the base type."
        )

    @abc.abstractmethod
    def build_place_order_instructions(self, order: Order) -> CombinableInstructions:
        raise NotImplementedError(
            "MarketInstructionBuilder.build_place_order_instructions() is not implemented on the base type."
        )

    @abc.abstractmethod
    def build_settle_instructions(self) -> CombinableInstructions:
        raise NotImplementedError(
            "MarketInstructionBuilder.build_settle_instructions() is not implemented on the base type."
        )

    @abc.abstractmethod
    def build_crank_instructions(
        self, addresses: typing.Sequence[PublicKey], limit: Decimal = Decimal(32)
    ) -> CombinableInstructions:
        raise NotImplementedError(
            "MarketInstructionBuilder.build_crank_instructions() is not implemented on the base type."
        )

    @abc.abstractmethod
    def build_redeem_instructions(self) -> CombinableInstructions:
        raise NotImplementedError(
            "MarketInstructionBuilder.build_redeem_instructions() is not implemented on the base type."
        )

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 MarketOperations class
#
# This abstracts the process of placing orders, providing a base class for specialised operations.
#
# It's abstracted because we may want to have different approaches to placing these
# orders - do we want to run them against the Serum orderbook? Do we want to run them against
# Mango groups?
#
# Whichever choice is made, the calling code shouldn't have to care. It should be able to
# use its `MarketOperations` class as simply as:
# ```
# market_operations.place_order(order)
# ```
#
class MarketOperations(metaclass=abc.ABCMeta):
    def __init__(self, market: LoadedMarket) -> None:
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.market: LoadedMarket = market

    @property
    def symbol(self) -> str:
        return self.market.fully_qualified_symbol

    @property
    def inventory_source(self) -> InventorySource:
        return self.market.inventory_source

    @abc.abstractmethod
    def cancel_order(
        self, order: Order, ok_if_missing: bool = False
    ) -> typing.Sequence[str]:
        raise NotImplementedError(
            "MarketOperations.cancel_order() is not implemented on the base type."
        )

    @abc.abstractmethod
    def place_order(
        self, order: Order, crank_limit: Decimal = Decimal(5)
    ) -> typing.Sequence[str]:
        raise NotImplementedError(
            "MarketOperations.place_order() is not implemented on the base type."
        )

    @abc.abstractmethod
    def load_orderbook(self) -> OrderBook:
        raise NotImplementedError(
            "MarketOperations.load_orders() is not implemented on the base type."
        )

    @abc.abstractmethod
    def load_my_orders(
        self, cutoff: typing.Optional[datetime] = utc_now()
    ) -> typing.Sequence[Order]:
        raise NotImplementedError(
            "MarketOperations.load_my_orders() is not implemented on the base type."
        )

    @abc.abstractmethod
    def settle(self) -> typing.Sequence[str]:
        raise NotImplementedError(
            "MarketOperations.settle() is not implemented on the base type."
        )

    @abc.abstractmethod
    def crank(self, limit: Decimal = Decimal(32)) -> typing.Sequence[str]:
        raise NotImplementedError(
            "MarketOperations.crank() is not implemented on the base type."
        )

    @abc.abstractmethod
    def create_openorders(self) -> PublicKey:
        raise NotImplementedError(
            "MarketOperations.create_openorders() is not implemented on the base type."
        )

    @abc.abstractmethod
    def ensure_openorders(self) -> PublicKey:
        raise NotImplementedError(
            "MarketOperations.ensure_openorders() is not implemented on the base type."
        )

    def market_buy(
        self, quantity: Decimal, max_slippage: Decimal
    ) -> typing.Sequence[str]:
        orderbook = self.load_orderbook()
        if orderbook.top_ask is None:
            raise Exception(f"Could not determine top ask on {orderbook.symbol}")

        top_ask = orderbook.top_ask.price

        increase_factor = Decimal(1) + max_slippage
        price = top_ask * increase_factor
        self._logger.info(f"Price {price} - adjusted by {max_slippage} from {top_ask}")

        order = Order.from_values(Side.BUY, price, quantity, OrderType.IOC)
        return self.place_order(order)

    def market_sell(
        self, quantity: Decimal, max_slippage: Decimal
    ) -> typing.Sequence[str]:
        orderbook = self.load_orderbook()
        if orderbook.top_bid is None:
            raise Exception(f"Could not determine top bid on {orderbook.symbol}")

        top_bid = orderbook.top_bid.price

        decrease_factor = Decimal(1) - max_slippage
        price = top_bid * decrease_factor
        self._logger.info(f"Price {price} - adjusted by {max_slippage} from {top_bid}")

        order = Order.from_values(Side.SELL, price, quantity, OrderType.IOC)
        return self.place_order(order)

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 NullMarketInstructionBuilder class
#
# A null, no-op, dry-run trade executor that can be plugged in anywhere a `MarketInstructionBuilder`
# is expected, but which will not actually trade.
#
class NullMarketInstructionBuilder(MarketInstructionBuilder):
    def __init__(self, symbol: str) -> None:
        super().__init__()
        self.symbol: str = symbol

    def build_cancel_order_instructions(
        self, order: Order, ok_if_missing: bool = False
    ) -> CombinableInstructions:
        return CombinableInstructions.empty()

    def build_place_order_instructions(self, order: Order) -> CombinableInstructions:
        return CombinableInstructions.empty()

    def build_settle_instructions(self) -> CombinableInstructions:
        return CombinableInstructions.empty()

    def build_crank_instructions(
        self, addresses: typing.Sequence[PublicKey], limit: Decimal = Decimal(32)
    ) -> CombinableInstructions:
        return CombinableInstructions.empty()

    def build_redeem_instructions(self) -> CombinableInstructions:
        return CombinableInstructions.empty()

    def __str__(self) -> str:
        return f"« NullMarketInstructionBuilder {self.symbol} »"


# # 🥭 NullMarketOperations class
#
# A null, no-op, dry-run trade executor that can be plugged in anywhere a `MarketOperations`
# is expected, but which will not actually trade.
#
class NullMarketOperations(MarketOperations):
    def __init__(self, market: LoadedMarket) -> None:
        super().__init__(market)

    def cancel_order(
        self, order: Order, ok_if_missing: bool = False
    ) -> typing.Sequence[str]:
        self._logger.info(f"[Dry Run] Not cancelling order {order}.")
        return [""]

    def place_order(
        self, order: Order, crank_limit: Decimal = Decimal(5)
    ) -> typing.Sequence[str]:
        self._logger.info(f"[Dry Run] Not placing order {order}.")
        return []

    def load_orderbook(self) -> OrderBook:
        return OrderBook(
            self.market.fully_qualified_symbol, NullLotSizeConverter(), [], []
        )

    def load_my_orders(
        self, cutoff: typing.Optional[datetime] = utc_now()
    ) -> typing.Sequence[Order]:
        return []

    def settle(self) -> typing.Sequence[str]:
        return []

    def crank(self, limit: Decimal = Decimal(32)) -> typing.Sequence[str]:
        return []

    def create_openorders(self) -> PublicKey:
        return SYSTEM_PROGRAM_ADDRESS

    def ensure_openorders(self) -> PublicKey:
        return SYSTEM_PROGRAM_ADDRESS

    def market_buy(
        self, quantity: Decimal, max_slippage: Decimal
    ) -> typing.Sequence[str]:
        self._logger.info(
            f"[Dry Run] Not market buying {quantity} with max slippage {max_slippage}."
        )
        return []

    def market_sell(
        self, quantity: Decimal, max_slippage: Decimal
    ) -> typing.Sequence[str]:
        self._logger.info(
            f"[Dry Run] Not market selling {quantity} with max slippage {max_slippage}."
        )
        return []

    def __str__(self) -> str:
        return f"""« NullMarketOperations [{self.market.fully_qualified_symbol}] »"""
