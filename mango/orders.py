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

from decimal import Decimal
from pyserum.market.types import Order as PySerumOrder
from solana.publickey import PublicKey

from .constants import SYSTEM_PROGRAM_ADDRESS
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
class Order(typing.NamedTuple):
    id: int
    client_id: int
    owner: PublicKey
    side: Side
    price: Decimal
    quantity: Decimal
    order_type: OrderType

    @staticmethod
    def read_sequence_number(id: int) -> Decimal:
        id_bytes = id.to_bytes(16, byteorder="little", signed=False)
        low_order = id_bytes[:8]
        return Decimal(int.from_bytes(low_order, 'little', signed=False))

    @staticmethod
    def read_price(id: int) -> Decimal:
        id_bytes = id.to_bytes(16, byteorder="little", signed=False)
        high_order = id_bytes[8:]
        return Decimal(int.from_bytes(high_order, 'little', signed=False))

    # Returns an identical order with the ID changed.
    def with_id(self, id: int) -> "Order":
        return Order(id=id, side=self.side, price=self.price, quantity=self.quantity,
                     client_id=self.client_id, owner=self.owner, order_type=self.order_type)

    # Returns an identical order with the Client ID changed.
    def with_client_id(self, client_id: int) -> "Order":
        return Order(id=self.id, side=self.side, price=self.price, quantity=self.quantity,
                     client_id=client_id, owner=self.owner, order_type=self.order_type)

    # Returns an identical order with the price changed.
    def with_price(self, price: Decimal) -> "Order":
        return Order(id=self.id, side=self.side, price=price, quantity=self.quantity,
                     client_id=self.client_id, owner=self.owner, order_type=self.order_type)

    # Returns an identical order with the quantity changed.
    def with_quantity(self, quantity: Decimal) -> "Order":
        return Order(id=self.id, side=self.side, price=self.price, quantity=quantity,
                     client_id=self.client_id, owner=self.owner, order_type=self.order_type)

    # Returns an identical order with the owner changed.
    def with_owner(self, owner: PublicKey) -> "Order":
        return Order(id=self.id, side=self.side, price=self.price, quantity=self.quantity,
                     client_id=self.client_id, owner=owner, order_type=self.order_type)

    @staticmethod
    def from_serum_order(serum_order: PySerumOrder) -> "Order":
        price = Decimal(serum_order.info.price)
        quantity = Decimal(serum_order.info.size)
        side = Side.from_value(serum_order.side)
        order = Order(id=serum_order.order_id, side=side, price=price, quantity=quantity,
                      client_id=serum_order.client_id, owner=serum_order.open_order_address,
                      order_type=OrderType.UNKNOWN)
        return order

    @staticmethod
    def from_basic_info(side: Side, price: Decimal, quantity: Decimal, order_type: OrderType = OrderType.UNKNOWN) -> "Order":
        order = Order(id=0, side=side, price=price, quantity=quantity, client_id=0,
                      owner=SYSTEM_PROGRAM_ADDRESS, order_type=order_type)
        return order

    @staticmethod
    def from_ids(id: int, client_id: int, side: Side = Side.BUY, price: Decimal = Decimal(0), quantity: Decimal = Decimal(0)) -> "Order":
        return Order(id=id, client_id=client_id, owner=SYSTEM_PROGRAM_ADDRESS, side=side, price=price, quantity=quantity, order_type=OrderType.UNKNOWN)

    def __str__(self) -> str:
        owner: str = ""
        if self.owner != SYSTEM_PROGRAM_ADDRESS:
            owner = f"[{self.owner}] "
        order_type: str = ""
        if self.order_type != OrderType.UNKNOWN:
            order_type = f" {self.order_type}"
        return f"« Order {owner}{self.side} for {self.quantity:,.8f} at {self.price:.8f} [ID: {self.id} / {self.client_id}]{order_type} »"

    def __repr__(self) -> str:
        return f"{self}"


class OrderBook:
    def __init__(self, symbol: str, lot_size_converter: LotSizeConverter, bids: typing.Sequence[Order], asks: typing.Sequence[Order]) -> None:
        self.symbol: str = symbol
        self.__lot_size_converter: LotSizeConverter = lot_size_converter
        self.__bids: typing.Sequence[Order] = []
        self.__asks: typing.Sequence[Order] = []
        self.bids = bids
        self.asks = asks

    @property
    def bids(self) -> typing.Sequence[Order]:
        return self.__bids

    @bids.setter
    def bids(self, bids: typing.Sequence[Order]) -> None:
        """ Sort bids high to low, so best bid is at index 0 """
        bids_list: typing.List[Order] = list(bids)
        bids_list.sort(key=lambda order: order.id, reverse=True)
        self.__bids = bids_list

    @property
    def asks(self) -> typing.Sequence[Order]:
        return self.__asks

    @asks.setter
    def asks(self, asks: typing.Sequence[Order]) -> None:
        """ Sets asks low to high, so best ask is at index 0"""
        asks_list: typing.List[Order] = list(asks)
        asks_list.sort(key=lambda order: order.id)
        self.__asks = asks_list

    # The top bid is the highest price someone is willing to pay to BUY
    @property
    def top_bid(self) -> typing.Optional[Order]:
        if self.bids and len(self.bids) > 0:
            # Top-of-book is always at index 0 for us.
            return self.bids[0]
        return None

    # The top ask is the lowest price someone is willing to pay to SELL
    @property
    def top_ask(self) -> typing.Optional[Order]:
        if self.asks and len(self.asks) > 0:
            # Top-of-book is always at index 0 for us.
            return self.asks[0]
        return None

    # The mid price is halfway between the best bid and best ask.
    @property
    def mid_price(self) -> typing.Optional[Decimal]:
        if self.top_bid is not None and self.top_ask is not None:
            return (self.top_bid.price + self.top_ask.price) / 2
        elif self.top_bid is not None:
            return self.top_bid.price
        elif self.top_ask is not None:
            return self.top_ask.price
        return None

    @property
    def spread(self) -> Decimal:
        top_ask = self.top_ask
        top_bid = self.top_bid
        if top_ask is None or top_bid is None:
            return Decimal(0)
        else:
            return top_ask.price - top_bid.price

    def to_dataframe(self) -> pandas.DataFrame:
        column_mapper = {
            "id": "Id",
            "client_id": "ClientId",
            "owner": "Owner",
            "side": "Side",
            "price": "Price",
            "quantity": "Quantity"
        }

        frame: pandas.DataFrame = pandas.DataFrame([*reversed(self.bids), *self.asks])
        frame = frame.drop(["order_type"], axis=1)
        frame = frame.rename(mapper=column_mapper, axis=1, copy=True)
        frame["Price"] = pandas.to_numeric(frame["Price"])
        frame["QuantityLots"] = frame["Quantity"].apply(self.__lot_size_converter.base_size_number_to_lots)
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

        return frame.groupby("Price").agg({"PriceLots": "first", "Side": "first", "Quantity": "sum", "QuantityLots": "sum"})

    def to_l3_dataframe(self) -> pandas.DataFrame:
        return self.to_dataframe()

    def __str__(self) -> str:
        def _order_to_str(order: Order) -> str:
            quantity = f"{order.quantity:,.8f}"
            price = f"{order.price:,.8f}"
            return f"{order.side} {quantity:>20} at {price:>20}"
        orders_to_show = 5
        lines = []
        for counter in range(orders_to_show):
            bid = _order_to_str(self.bids[counter]) if len(self.bids) > counter else ""
            ask = _order_to_str(self.asks[counter]) if len(self.asks) > counter else ""
            lines += [f"{bid:50} :: {ask}"]

        text = "\n\t".join(lines)
        spread_description = "N/A"
        if self.spread != 0 and self.top_bid is not None:
            spread_percentage = (self.spread / self.top_bid.price)
            spread_description = f"{self.spread:,.8f}, {spread_percentage:,.3%}"
        return f"« OrderBook {self.symbol} [spread: {spread_description}]\n\t{text}\n»"

    def __repr__(self) -> str:
        return f"{self}"
