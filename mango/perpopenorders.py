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

from .layouts import layouts
from .openorders import PlacedOrder


# # 🥭 PerpOpenOrders class
#
class PerpOpenOrders:
    def __init__(self, bids_quantity: Decimal, asks_quantity: Decimal, free_slot_bits: Decimal,
                 is_bid_bits: Decimal, placed_orders: typing.Sequence[PlacedOrder]):
        self.bids_quantity: Decimal = bids_quantity
        self.asks_quantity: Decimal = asks_quantity
        self.free_slot_bits: Decimal = free_slot_bits
        self.is_bid_bits: Decimal = is_bid_bits
        self.placed_orders: typing.Sequence[PlacedOrder] = placed_orders

    @staticmethod
    def from_layout(layout: layouts.PERP_OPEN_ORDERS) -> "PerpOpenOrders":
        bids_quantity: Decimal = layout.bids_quantity
        asks_quantity: Decimal = layout.asks_quantity
        free_slot_bits: Decimal = layout.free_slot_bits
        is_bid_bits: Decimal = layout.is_bid_bits

        placed_orders = PlacedOrder.build_from_open_orders_data(
            layout.free_slot_bits, layout.is_bid_bits, layout.orders, layout.client_order_ids)
        return PerpOpenOrders(bids_quantity, asks_quantity, free_slot_bits, is_bid_bits, placed_orders)

    def __str__(self) -> str:
        placed_orders = "\n        ".join(map(str, self.placed_orders)) or "None"

        return f"""« 𝙿𝚎𝚛𝚙𝙾𝚙𝚎𝚗𝙾𝚛𝚍𝚎𝚛𝚜
    Bids Quantity: {self.bids_quantity}
    Asks Quantity: {self.asks_quantity}
    Orders:
        {placed_orders}
»"""
