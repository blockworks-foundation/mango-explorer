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

from .orders import Side

# # 🥭 PlacedOrder tuple
#
# A `PlacedOrder` is a representation of all the data available from an Open Orders account pertaining to a
# particular order.
#
# The information is usually split across 3 collections - 'is bid', 'orders' and 'client ID's. That can be a
# little awkward to use, so this tuple packages it all together, per order.
#


class PlacedOrder(typing.NamedTuple):
    id: int
    client_id: int
    side: Side

    @staticmethod
    def build_from_open_orders_data(free_slot_bits: Decimal, is_bid_bits: Decimal, order_ids: typing.Sequence[Decimal], client_order_ids: typing.Sequence[Decimal]):
        int_free_slot_bits = int(free_slot_bits)
        int_is_bid_bits = int(is_bid_bits)
        placed_orders: typing.List[PlacedOrder] = []
        for index in range(len(order_ids)):
            if not (int_free_slot_bits & (1 << index)):
                order_id = int(order_ids[index])
                client_id = int(client_order_ids[index])
                side = Side.BUY if int_is_bid_bits & (1 << index) else Side.SELL
                placed_orders += [PlacedOrder(id=order_id, client_id=client_id, side=side)]
        return placed_orders

    def __repr__(self) -> str:
        return f"{self}"

    def __str__(self) -> str:
        return f"« 𝙿𝚕𝚊𝚌𝚎𝚍𝙾𝚛𝚍𝚎𝚛 {self.side} [{self.id}] {self.client_id} »"


# # 🥭 PlacedOrdersContainer protocol
#
# The `PlacedOrdersContainer` protocol exposes commonality between the regular Serum `OpenOrders` class and the
# internally-different `PerpOpenOrders` class. Both have their own `placed_orders` member, but are otherwise
# different enough that a common abstract base class would be a bit kludgy.
#
class PlacedOrdersContainer(typing.Protocol):
    placed_orders: typing.Sequence[PlacedOrder]
