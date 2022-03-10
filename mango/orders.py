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


import enum
import pandas
import pyserum.enums
import typing

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from pyserum.market.types import Order as PySerumOrder
from solana.publickey import PublicKey

from .constants import SYSTEM_PROGRAM_ADDRESS
from .datetimes import utc_now, datetime_from_timestamp
from .lotsizeconverter import LotSizeConverter


# # 🥭 Orders
#
# This file holds some basic common orders data types.
#


# # 🥭 Side enum
#
# Is an order a Buy or a Sell?
#
class Side(enum.Enum):
    # We use strings here so that argparse can work with these as parameters.
    BUY = "BUY"
    SELL = "SELL"

    @staticmethod
    def from_value(value: pyserum.enums.Side) -> "Side":
        converted: pyserum.enums.Side = pyserum.enums.Side(int(value))
        return Side.BUY if converted == pyserum.enums.Side.BUY else Side.SELL

    def to_serum(self) -> pyserum.enums.Side:
        return pyserum.enums.Side.BUY if self == Side.BUY else pyserum.enums.Side.SELL

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 OrderType enum
#
# 3 order types are supported: Limit (most common), IOC (immediate or cancel - not placed on the order book
# so if it doesn't get filled immediately it is cancelled), and Post Only (only ever places orders on the
# orderbook - if this would be filled immediately without being placed on the order book it is cancelled).
#
class OrderType(enum.Enum):
    # We use strings here so that argparse can work with these as parameters.
    UNKNOWN = "UNKNOWN"
    LIMIT = "LIMIT"
    IOC = "IOC"
    POST_ONLY = "POST_ONLY"
    MARKET = "MARKET"
    POST_ONLY_SLIDE = "POST_ONLY_SLIDE"

    @staticmethod
    def from_value(value: Decimal) -> "OrderType":
        # From: https://github.com/blockworks-foundation/mango-v3/blob/0c4d26e3e32821d871c5e5986edafbf694a44137/program/src/matching.rs#L212
        # pub enum OrderType {
        #     Limit = 0,
        #     ImmediateOrCancel = 1,
        #     PostOnly = 2,
        #     Market = 3,
        #     PostOnlySlide = 4, // ***
        # }
        if value == 0:
            return OrderType.LIMIT
        elif value == 1:
            return OrderType.IOC
        elif value == 2:
            return OrderType.POST_ONLY
        elif value == 3:
            return OrderType.MARKET
        elif value == 4:
            return OrderType.POST_ONLY_SLIDE

        return OrderType.LIMIT

    def to_serum(self) -> pyserum.enums.OrderType:
        if self == OrderType.IOC:
            return pyserum.enums.OrderType.IOC
        elif self == OrderType.POST_ONLY:
            return pyserum.enums.OrderType.POST_ONLY
        elif self == OrderType.POST_ONLY_SLIDE:
            # Best we can do in this situation
            return pyserum.enums.OrderType.POST_ONLY
        else:
            return pyserum.enums.OrderType.LIMIT

    def to_perp(self) -> int:
        # From: https://github.com/blockworks-foundation/mango-v3/blob/0c4d26e3e32821d871c5e5986edafbf694a44137/program/src/matching.rs#L212
        # pub enum OrderType {
        #     Limit = 0,
        #     ImmediateOrCancel = 1,
        #     PostOnly = 2,
        #     Market = 3,
        #     PostOnlySlide = 4, // ***
        # }
        if self == OrderType.LIMIT:
            return 0
        elif self == OrderType.IOC:
            return 1
        elif self == OrderType.POST_ONLY:
            return 2
        elif self == OrderType.MARKET:
            return 3
        elif self == OrderType.POST_ONLY_SLIDE:
            return 4
        else:
            return -1

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"{self}"


# # 🥭 Order named tuple
#
# A package that encapsulates common information about an order.
#
@dataclass(frozen=True)
class Order:
    DefaultMatchLimit: typing.ClassVar[int] = 20
    NoExpiration: typing.ClassVar[datetime] = datetime_from_timestamp(0)
    id: int
    client_id: int
    owner: PublicKey
    side: Side
    price: Decimal
    quantity: Decimal
    order_type: OrderType
    reduce_only: bool = False
    timestamp: typing.Optional[datetime] = None
    expiration: datetime = NoExpiration
    match_limit: int = DefaultMatchLimit

    @staticmethod
    def read_sequence_number(id: int) -> Decimal:
        id_bytes = id.to_bytes(16, byteorder="little", signed=False)
        low_order = id_bytes[:8]
        return Decimal(int.from_bytes(low_order, "little", signed=False))

    @staticmethod
    def read_price(id: int) -> Decimal:
        id_bytes = id.to_bytes(16, byteorder="little", signed=False)
        high_order = id_bytes[8:]
        return Decimal(int.from_bytes(high_order, "little", signed=False))

    def _emoji_marker_at(self, cutoff: datetime) -> str:
        if self.is_expired_at(cutoff):
            return "⛔"
        elif self.expiration != Order.NoExpiration:
            return "⏰"
        return "📌"

    def is_expired_at(self, cutoff: typing.Optional[datetime]) -> bool:
        if (
            (cutoff is None)
            or (self.expiration == Order.NoExpiration)
            or (self.expiration > cutoff)
        ):
            return False
        return True

    # Returns an identical order with the provided values changed.
    def with_update(
        self,
        id: typing.Optional[int] = None,
        client_id: typing.Optional[int] = None,
        owner: typing.Optional[PublicKey] = None,
        side: typing.Optional[Side] = None,
        price: typing.Optional[Decimal] = None,
        quantity: typing.Optional[Decimal] = None,
        order_type: typing.Optional[OrderType] = None,
        reduce_only: typing.Optional[bool] = None,
        timestamp: typing.Optional[datetime] = None,
        expiration: typing.Optional[datetime] = None,
        match_limit: typing.Optional[int] = None,
    ) -> "Order":
        return Order(
            id=id if id is not None else self.id,
            client_id=client_id if client_id is not None else self.client_id,
            owner=owner if owner is not None else self.owner,
            side=side if side is not None else self.side,
            price=price if price is not None else self.price,
            quantity=quantity if quantity is not None else self.quantity,
            order_type=order_type if order_type is not None else self.order_type,
            reduce_only=reduce_only if reduce_only is not None else self.reduce_only,
            timestamp=timestamp if timestamp is not None else self.timestamp,
            expiration=expiration if expiration is not None else self.expiration,
            match_limit=match_limit if match_limit is not None else self.match_limit,
        )

    @staticmethod
    def from_serum_order(serum_order: PySerumOrder) -> "Order":
        price = Decimal(serum_order.info.price)
        quantity = Decimal(serum_order.info.size)
        side = Side.from_value(serum_order.side)
        order = Order(
            id=serum_order.order_id,
            side=side,
            price=price,
            quantity=quantity,
            client_id=serum_order.client_id,
            owner=serum_order.open_order_address,
            order_type=OrderType.UNKNOWN,
        )
        return order

    @staticmethod
    def from_values(
        side: Side,
        price: Decimal,
        quantity: Decimal,
        order_type: OrderType = OrderType.UNKNOWN,
        id: int = 0,
        client_id: int = 0,
        owner: PublicKey = SYSTEM_PROGRAM_ADDRESS,
        reduce_only: bool = False,
        timestamp: typing.Optional[datetime] = None,
        expiration: datetime = NoExpiration,
        match_limit: int = 20,
    ) -> "Order":
        order = Order(
            id=id,
            side=side,
            price=price,
            quantity=quantity,
            client_id=client_id,
            owner=owner,
            order_type=order_type,
            reduce_only=reduce_only,
            timestamp=timestamp,
            expiration=expiration,
            match_limit=match_limit,
        )
        return order

    @staticmethod
    def from_ids(
        id: int,
        client_id: int,
        side: Side = Side.BUY,
        price: Decimal = Decimal(0),
        quantity: Decimal = Decimal(0),
    ) -> "Order":
        return Order(
            id=id,
            client_id=client_id,
            owner=SYSTEM_PROGRAM_ADDRESS,
            side=side,
            price=price,
            quantity=quantity,
            order_type=OrderType.UNKNOWN,
            reduce_only=False,
            timestamp=None,
            expiration=Order.NoExpiration,
            match_limit=20,
        )

    @staticmethod
    def build_absolute_expiration(
        expire_seconds: typing.Optional[Decimal],
    ) -> datetime:
        if expire_seconds is None or expire_seconds <= Decimal(0):
            return Order.NoExpiration

        return utc_now() + timedelta(seconds=float(expire_seconds))

    def __str__(self) -> str:
        owner: str = ""
        if self.owner != SYSTEM_PROGRAM_ADDRESS:
            owner = f"[{self.owner}] "
        order_type: str = ""
        if self.order_type != OrderType.UNKNOWN:
            order_type = f" {self.order_type}"
        marker = self._emoji_marker_at(utc_now())
        return f"« Order {marker} {owner}{self.side} {self.quantity:,.8f} at {self.price:.8f} [ID: {self.id} / {self.client_id}]{order_type}{' reduceOnly' if self.reduce_only else ''} »"

    def __repr__(self) -> str:
        return f"{self}"


class OrderBook:
    def __init__(
        self,
        symbol: str,
        lot_size_converter: LotSizeConverter,
        bids: typing.Sequence[Order],
        asks: typing.Sequence[Order],
    ) -> None:
        self.symbol: str = symbol
        self.__lot_size_converter: LotSizeConverter = lot_size_converter
        self.__bids: typing.Sequence[Order] = []
        self.__asks: typing.Sequence[Order] = []
        self.bids = bids
        self.asks = asks

    @property
    def bids(self) -> typing.Sequence[Order]:
        return self.bids_at(cutoff=utc_now())

    @bids.setter
    def bids(self, bids: typing.Sequence[Order]) -> None:
        """Sort bids high to low, so best bid is at index 0"""
        bids_list: typing.List[Order] = list(bids)
        bids_list.sort(key=lambda order: order.id, reverse=True)
        self.__bids = bids_list

    @property
    def asks(self) -> typing.Sequence[Order]:
        return self.asks_at(cutoff=utc_now())

    @asks.setter
    def asks(self, asks: typing.Sequence[Order]) -> None:
        """Sets asks low to high, so best ask is at index 0"""
        asks_list: typing.List[Order] = list(asks)
        asks_list.sort(key=lambda order: order.id)
        self.__asks = asks_list

    # The top bid is the highest price someone is willing to pay to BUY
    @property
    def top_bid(self) -> typing.Optional[Order]:
        return self.top_bid_at(cutoff=utc_now())

    # The top ask is the lowest price someone is willing to pay to SELL
    @property
    def top_ask(self) -> typing.Optional[Order]:
        return self.top_ask_at(cutoff=utc_now())

    # The mid price is halfway between the best bid and best ask.
    @property
    def mid_price(self) -> typing.Optional[Decimal]:
        return self.mid_price_at(cutoff=utc_now())

    @property
    def spread(self) -> Decimal:
        return self.spread_at(cutoff=utc_now())

    def bids_at(
        self, cutoff: typing.Optional[datetime] = None
    ) -> typing.Sequence[Order]:
        return list([o for o in self.__bids if not o.is_expired_at(cutoff)])

    def asks_at(
        self, cutoff: typing.Optional[datetime] = None
    ) -> typing.Sequence[Order]:
        return list([o for o in self.__asks if not o.is_expired_at(cutoff)])

    def orders_at(
        self, cutoff: typing.Optional[datetime] = None
    ) -> typing.Sequence[Order]:
        return [*self.bids_at(cutoff), *self.asks_at(cutoff)]

    # The top bid is the highest price someone is willing to pay to BUY
    def top_bid_at(
        self, cutoff: typing.Optional[datetime] = None
    ) -> typing.Optional[Order]:
        bids = self.bids_at(cutoff)
        if bids and len(bids) > 0:
            # Top-of-book is always at index 0 for us.
            return bids[0]
        return None

    # The top ask is the lowest price someone is willing to pay to SELL
    def top_ask_at(
        self, cutoff: typing.Optional[datetime] = None
    ) -> typing.Optional[Order]:
        asks = self.asks_at(cutoff)
        if asks and len(asks) > 0:
            # Top-of-book is always at index 0 for us.
            return asks[0]
        return None

    # The mid price is halfway between the best bid and best ask.
    def mid_price_at(
        self, cutoff: typing.Optional[datetime] = None
    ) -> typing.Optional[Decimal]:
        top_bid = self.top_bid_at(cutoff)
        top_ask = self.top_ask_at(cutoff)
        if top_bid is not None and top_ask is not None:
            return (top_bid.price + top_ask.price) / 2
        elif top_bid is not None:
            return top_bid.price
        elif top_ask is not None:
            return top_ask.price
        return None

    def spread_at(self, cutoff: typing.Optional[datetime] = None) -> Decimal:
        top_ask = self.top_ask_at(cutoff)
        top_bid = self.top_bid_at(cutoff)
        if top_ask is None or top_bid is None:
            return Decimal(0)
        else:
            return top_ask.price - top_bid.price

    def all_orders_for_owner(
        self, owner_address: PublicKey, cutoff: typing.Optional[datetime] = None
    ) -> typing.Sequence[Order]:
        return list([o for o in self.orders_at(cutoff) if o.owner == owner_address])

    def to_dataframe(self) -> pandas.DataFrame:
        column_mapper = {
            "id": "Id",
            "client_id": "ClientId",
            "owner": "Owner",
            "side": "Side",
            "price": "Price",
            "quantity": "Quantity",
            "timestamp": "Timestamp",
            "expiration": "Expiration",
        }

        frame: pandas.DataFrame = pandas.DataFrame([*reversed(self.bids), *self.asks])
        frame = frame.drop(["order_type"], axis=1)
        frame = frame.rename(mapper=column_mapper, axis=1, copy=True)
        frame["Price"] = pandas.to_numeric(frame["Price"])
        frame["QuantityLots"] = frame["Quantity"].apply(
            self.__lot_size_converter.base_size_number_to_lots
        )
        frame["Quantity"] = pandas.to_numeric(frame["Quantity"])
        frame["PriceLots"] = pandas.to_numeric(frame["Id"].apply(Order.read_price))
        frame["SequenceNumber"] = frame["Id"].apply(Order.read_sequence_number)

        return frame

    def to_l1_dataframe(self) -> pandas.DataFrame:
        frame: pandas.DataFrame = self.to_l2_dataframe()
        buys = frame[(frame["Side"] == Side.BUY)]
        sells = frame[(frame["Side"] == Side.SELL)]
        top = frame.loc[[buys["PriceLots"].idxmax(), sells["PriceLots"].idxmin()]]
        return typing.cast(pandas.DataFrame, top)

    def to_l2_dataframe(self) -> pandas.DataFrame:
        frame: pandas.DataFrame = self.to_dataframe()

        return frame.groupby("Price").agg(
            {
                "PriceLots": "first",
                "Side": "first",
                "Quantity": "sum",
                "QuantityLots": "sum",
            }
        )

    def to_l3_dataframe(self) -> pandas.DataFrame:
        return self.to_dataframe()

    def __str__(self) -> str:
        def _order_to_str(order: Order) -> str:
            marker = order._emoji_marker_at(utc_now())
            quantity = f"{order.quantity:,.8f}"
            price = f"{order.price:,.8f}"
            return f"{marker} {order.side} {quantity:>20} at {price:>20}"

        orders_to_show = 5
        lines = []
        for counter in range(orders_to_show):
            bid = _order_to_str(self.bids[counter]) if len(self.bids) > counter else ""
            ask = _order_to_str(self.asks[counter]) if len(self.asks) > counter else ""
            lines += [f"{bid:50} :: {ask}"]

        text = "\n\t".join(lines)
        spread_description = "N/A"
        if self.spread != 0 and self.top_bid is not None:
            spread_percentage = self.spread / self.top_bid.price
            spread_description = f"{self.spread:,.8f}, {spread_percentage:,.3%}"
        return f"« OrderBook {self.symbol} [spread: {spread_description}]\n\t{text}\n»"

    def __repr__(self) -> str:
        return f"{self}"
