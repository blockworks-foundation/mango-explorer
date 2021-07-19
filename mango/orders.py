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
from pyserum.market.types import Order as SerumOrder
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

    @staticmethod
    def from_serum_order(serum_order: SerumOrder) -> "Order":
        price = Decimal(serum_order.info.price)
        quantity = Decimal(serum_order.info.size)
        side = Side.BUY if serum_order.side == pyserum.enums.Side.BUY else Side.SELL
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
