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

from .pairwiseelement import PairwiseElement
from ...modelstate import ModelState


# # 🥭 FixedPositionSizeElement class
#
# Ignores any input `Order`s (so probably best at the head of the chain). Builds orders using a fixed spread
# value and a fixed position size value.
#
class FixedPositionSizeElement(PairwiseElement):
    def __init__(self, position_sizes: typing.Sequence[Decimal]) -> None:
        super().__init__()
        self.position_sizes: typing.Sequence[Decimal] = position_sizes

    @staticmethod
    def add_command_line_parameters(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--fixedpositionsize-value", type=Decimal, action="append",
                            help="fixed value to use as the position size. Can be specified multiple times for multiple levels of BUYs and SELLs.")

    @staticmethod
    def from_command_line_parameters(args: argparse.Namespace) -> "FixedPositionSizeElement":
        if args.fixedpositionsize_value is None:
            raise Exception("No position-size value specified. Try the --fixedpositionsize-value parameter?")

        position_sizes: typing.Sequence[Decimal] = args.fixedpositionsize_value
        return FixedPositionSizeElement(position_sizes)

    def process_order_pair(self, context: mango.Context, model_state: ModelState, index: int, buy: typing.Optional[mango.Order], sell: typing.Optional[mango.Order]) -> typing.Tuple[typing.Optional[mango.Order], typing.Optional[mango.Order]]:
        # If no position size is explicitly specified for this element, just use the last specified size.
        size: Decimal = self.position_sizes[index] if index < len(self.position_sizes) else self.position_sizes[-1]
        new_buy: typing.Optional[mango.Order] = None
        new_sell: typing.Optional[mango.Order] = None
        if buy is not None:
            new_buy = buy.with_quantity(size)
            self._logger.debug(f"""Order change - using fixed position size of {size}:
    Old: {buy}
    New: {new_buy}""")

        if sell is not None:
            new_sell = sell.with_quantity(size)
            self._logger.debug(f"""Order change - using fixed position size of {size}:
    Old: {sell}
    New: {new_sell}""")

        return new_buy, new_sell

    def __str__(self) -> str:
        return f"« FixedPositionSizeElement using position sizes: {self.position_sizes} »"
