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

from .element import Element
from ...modelstate import ModelState


# # 🥭 FixedPositionSizeElement class
#
# Ignores any input `Order`s (so probably best at the head of the chain). Builds orders using a fixed spread
# value and a fixed position size value.
#
class FixedPositionSizeElement(Element):
    def __init__(self, position_sizes: typing.Sequence[Decimal]):
        super().__init__()
        self.position_sizes: typing.Sequence[Decimal] = position_sizes

    @staticmethod
    def add_command_line_parameters(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--fixedpositionsize-value", type=Decimal, action="append",
                            help="fixed value to use as the position size (only works well with a single 'level' of orders - one BUY and one SELL)")

    @staticmethod
    def from_command_line_parameters(args: argparse.Namespace) -> "FixedPositionSizeElement":
        if args.fixedpositionsize_value is None:
            raise Exception("No position-size value specified. Try the --fixedpositionsize-value parameter?")

        position_sizes: typing.Sequence[Decimal] = args.fixedpositionsize_value
        return FixedPositionSizeElement(position_sizes)

    # This is the simple case. If there is only one fixed position size, just apply it to every order.
    def _single_fixed_position_size(self, position_size: Decimal, orders: typing.Sequence[mango.Order]) -> typing.Sequence[mango.Order]:
        new_orders: typing.List[mango.Order] = []
        for order in orders:
            new_order: mango.Order = order.with_quantity(position_size)

            self.logger.debug(f"""Order change - using fixed position size of {position_size}:
    Old: {order}
    New: {new_order}""")
            new_orders += [new_order]

        return new_orders

    # This is the complicated case. If multiple levels are specified, apply them in order.
    #
    # But 'in order' is complicated. The way it will be expected to work is:
    # * First BUY and first SELL get the first fixed position size
    # * Second BUY and second SELL get the second fixed position size
    # * Third BUY and third SELL get the third fixed position size
    # * etc.
    # But (another but!) 'first' means closest to the top of the book to people, not necessarily
    # first in the incoming order list.
    #
    # We want to meet that expected approach, so we'll:
    # * Split the list into BUYs and SELLs
    # * Sort the two lists so closest to top-of-book is at index 0
    # * Process both lists together, setting the appropriate fixed position sizes
    def _multiple_fixed_position_size(self, position_sizes: typing.Sequence[Decimal], orders: typing.Sequence[mango.Order]) -> typing.Sequence[mango.Order]:
        buys: typing.List[mango.Order] = list([order for order in orders if order.side == mango.Side.BUY])
        buys.sort(key=lambda order: order.price, reverse=True)
        sells: typing.List[mango.Order] = list([order for order in orders if order.side == mango.Side.SELL])
        sells.sort(key=lambda order: order.price)

        pair_count: int = max(len(buys), len(sells))
        new_orders: typing.List[mango.Order] = []
        for index in range(pair_count):
            # If no position size is explicitly specified for this element, just use the last specified size.
            size: Decimal = position_sizes[index] if index < len(position_sizes) else position_sizes[-1]
            if index < len(buys):
                buy = buys[index]
                new_buy: mango.Order = buy.with_quantity(size)
                self.logger.debug(f"""Order change - using fixed position size of {size}:
    Old: {buy}
    New: {new_buy}""")
                new_orders += [new_buy]

            if index < len(sells):
                sell = sells[index]
                new_sell: mango.Order = sell.with_quantity(size)
                self.logger.debug(f"""Order change - using fixed position size of {size}:
    Old: {sell}
    New: {new_sell}""")
                new_orders += [new_sell]

        return new_orders

    def process(self, context: mango.Context, model_state: ModelState, orders: typing.Sequence[mango.Order]) -> typing.Sequence[mango.Order]:
        if len(self.position_sizes) == 1:
            return self._single_fixed_position_size(self.position_sizes[0], orders)
        return self._multiple_fixed_position_size(self.position_sizes, orders)

    def __str__(self) -> str:
        return f"« 𝙵𝚒𝚡𝚎𝚍𝙿𝚘𝚜𝚒𝚝𝚒𝚘𝚗𝚂𝚒𝚣𝚎𝙴𝚕𝚎𝚖𝚎𝚗𝚝 using position sizes: {self.position_sizes} »"
