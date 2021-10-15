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
import pyserum.enums
import typing

from decimal import Decimal
from pyserum.market.types import Order as PySerumOrder
from solana.publickey import PublicKey

from .constants import SYSTEM_PROGRAM_ADDRESS

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
        converted: pyserum.enums.OrderType = pyserum.enums.OrderType(int(value))
        if converted == pyserum.enums.OrderType.IOC:
            return OrderType.IOC
        elif converted == pyserum.enums.OrderType.POST_ONLY:
            return OrderType.POST_ONLY
        elif converted == pyserum.enums.OrderType.LIMIT:
            return OrderType.LIMIT
        return OrderType.UNKNOWN

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
    def from_ids(id: int, client_id: int, side: Side = Side.BUY) -> "Order":
        return Order(id=id, client_id=client_id, owner=SYSTEM_PROGRAM_ADDRESS, side=side, price=Decimal(0), quantity=Decimal(0), order_type=OrderType.UNKNOWN)

    def __str__(self) -> str:
        owner: str = ""
        if self.owner != SYSTEM_PROGRAM_ADDRESS:
            owner = f"[{self.owner}] "
        order_type: str = ""
        if self.order_type != OrderType.UNKNOWN:
            order_type = f" {self.order_type}"
        return f"« 𝙾𝚛𝚍𝚎𝚛 {owner}{self.side} for {self.quantity:,.8f} at {self.price:.8f} [ID: {self.id} / {self.client_id}]{order_type} »"

    def __repr__(self) -> str:
        return f"{self}"
