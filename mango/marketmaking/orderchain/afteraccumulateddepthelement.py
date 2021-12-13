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
    def __init__(self, depth: typing.Optional[Decimal], adjustment_ticks: Decimal = Decimal(1)) -> None:
        super().__init__()
        self.depth: typing.Optional[Decimal] = depth
        self.adjustment_ticks: Decimal = adjustment_ticks

    @staticmethod
    def add_command_line_parameters(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--afteraccumulateddepth-depth", type=Decimal,
                            help="optional fixed depth used to determine where in orderbook to place order. If not specified, the order quantity is used.")
        parser.add_argument("--afteraccumulateddepth-adjustment-ticks", type=Decimal, default=Decimal(1),
                            help="number of ticks above/below the accumulated depth to place the order. Default is 1 tick above for a SELL, 1 tick below for a BUY. Use 0 to specify placing the order AT the depth.")

    @staticmethod
    def from_command_line_parameters(args: argparse.Namespace) -> "AfterAccumulatedDepthElement":
        return AfterAccumulatedDepthElement(args.afteraccumulateddepth_depth, args.afteraccumulateddepth_adjustment_ticks)

    def _accumulated_quantity_exceeds_order(self, orders: typing.Sequence[mango.Order], owner: PublicKey, quantity: Decimal) -> typing.Optional[mango.Order]:
        accumulated_quantity: Decimal = Decimal(0)
        for order in orders:
            if order.owner != owner:
                accumulated_quantity += order.quantity
            if accumulated_quantity >= quantity:
                # Success!
                return order
        return None

    def process(self, context: mango.Context, model_state: ModelState, orders: typing.Sequence[mango.Order]) -> typing.Sequence[mango.Order]:
        new_orders: typing.List[mango.Order] = []
        adjustment: Decimal = self.adjustment_ticks * model_state.market.lot_size_converter.tick_size
        for order in orders:
            new_price: typing.Optional[Decimal] = None
            depth: Decimal = self.depth or order.quantity
            if order.side == mango.Side.BUY:
                place_below: typing.Optional[mango.Order] = self._accumulated_quantity_exceeds_order(
                    model_state.bids, model_state.order_owner, depth)
                if place_below is not None:
                    new_price = place_below.price - adjustment
            else:
                place_above: typing.Optional[mango.Order] = self._accumulated_quantity_exceeds_order(
                    model_state.asks, model_state.order_owner, depth)
                if place_above is not None:
                    new_price = place_above.price + adjustment

            if new_price is None:
                self._logger.debug(f"""Order change - no acceptable depth for quantity {depth} so removing:
    Old: {order}
    New: None""")
            else:
                new_order: mango.Order = order.with_price(new_price)
                self._logger.debug(f"""Order change - accumulated depth of {depth} is {self.adjustment_ticks} tick from {new_price}:
    Old: {order}
    New: {new_order}""")
                new_orders += [new_order]

        return new_orders

    def __str__(self) -> str:
        depth: str = f"{self.depth}" if self.depth is not None else "order quantity"
        return f"« AfterAccumulatedDepthElement [depth: {depth}, adjustment ticks: {self.adjustment_ticks}] »"
