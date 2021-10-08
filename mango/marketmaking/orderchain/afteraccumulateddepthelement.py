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

import argparse

import mango
import typing

from decimal import Decimal
from solana.publickey import PublicKey

from .element import Element
from ...modelstate import ModelState


# # 🥭 AfterAccumulatedDepthElement class
#
# Tries to place an order on the orderbook with sufficient quantity on orders between it and the mid-price.
#
# Basically, if an order is for quantity X then this element will start at the top of the book and move down
# orders until the accumulated quantity from orders is greater than the quantity of the desired order.
#
# If an order is for 1 BTC, the order will be priced so that there is at least 1 BTC's worth of orders between
# its price and the mid-price.
#
class AfterAccumulatedDepthElement(Element):
    def __init__(self):
        super().__init__()

    @staticmethod
    def add_command_line_parameters(parser: argparse.ArgumentParser) -> None:
        pass

    @staticmethod
    def from_command_line_parameters(args: argparse.Namespace) -> "AfterAccumulatedDepthElement":
        return AfterAccumulatedDepthElement()

    def _accumulated_quantity_exceeds_order(self, orders: typing.Sequence[mango.Order], owner: PublicKey, quantity: Decimal) -> typing.Optional[mango.Order]:
        accumulated_quantity: Decimal = Decimal(0)
        for order in orders:
            if order.owner != owner:
                accumulated_quantity += order.quantity
            if accumulated_quantity > quantity:
                # Success!
                return order
        return None

    def process(self, context: mango.Context, model_state: ModelState, orders: typing.Sequence[mango.Order]) -> typing.Sequence[mango.Order]:
        new_orders: typing.List[mango.Order] = []
        for order in orders:
            new_price: typing.Optional[Decimal] = None
            if order.side == mango.Side.BUY:
                place_below: typing.Optional[mango.Order] = self._accumulated_quantity_exceeds_order(
                    model_state.bids, model_state.order_owner, order.quantity)
                if place_below is not None:
                    new_price = place_below.price - model_state.market.lot_size_converter.tick_size
            else:
                place_above: typing.Optional[mango.Order] = self._accumulated_quantity_exceeds_order(
                    model_state.asks, model_state.order_owner, order.quantity)
                if place_above is not None:
                    new_price = place_above.price + model_state.market.lot_size_converter.tick_size

            if new_price is None:
                self.logger.debug(f"""Order change - no acceptable depth for quantity {order.quantity} so removing:
    Old: {order}
    New: None""")
            else:
                new_order: mango.Order = order.with_price(new_price)
                self.logger.debug(f"""Order change - accumulated depth of {order.quantity} is one tick from {new_price}:
    Old: {order}
    New: {new_order}""")
                new_orders += [new_order]

        return new_orders

    def __str__(self) -> str:
        return "« 𝙰𝚏𝚝𝚎𝚛𝙰𝚌𝚌𝚞𝚖𝚞𝚕𝚊𝚝𝚎𝚍𝙳𝚎𝚙𝚝𝚑𝙴𝚕𝚎𝚖𝚎𝚗𝚝 »"
