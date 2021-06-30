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
    size: Decimal

    @staticmethod
    def from_serum_order(serum_order: SerumOrder) -> "Order":
        price = Decimal(serum_order.info.price)
        size = Decimal(serum_order.info.size)
        side = Side.BUY if serum_order.side == pyserum.enums.Side.BUY else Side.SELL
        order = Order(id=serum_order.order_id, side=side, price=price, size=size,
                      client_id=serum_order.client_id, owner=serum_order.open_order_address)
        return order
