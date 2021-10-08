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
    def __init__(self, position_size: Decimal):
        super().__init__()
        self.position_size: Decimal = position_size

    @staticmethod
    def add_command_line_parameters(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--fixedpositionsize-value", type=Decimal,
                            help="fixed value to use as the position size (only works well with a single 'level' of orders - one BUY and one SELL)")

    @staticmethod
    def from_command_line_parameters(args: argparse.Namespace) -> "FixedPositionSizeElement":
        if args.fixedpositionsize_value is None:
            raise Exception("No position-size value specified. Try the --fixedpositionsize-value parameter?")

        position_size: Decimal = args.fixedpositionsize_value
        return FixedPositionSizeElement(position_size)

    def process(self, context: mango.Context, model_state: ModelState, orders: typing.Sequence[mango.Order]) -> typing.Sequence[mango.Order]:
        new_orders: typing.List[mango.Order] = []
        for order in orders:
            new_order: mango.Order = order.with_quantity(self.position_size)

            self.logger.debug(f"""Order change - using fixed position size of {self.position_size}:
    Old: {order}
    New: {new_order}""")
            new_orders += [new_order]

        return new_orders

    def __str__(self) -> str:
        return f"« 𝙵𝚒𝚡𝚎𝚍𝙿𝚘𝚜𝚒𝚝𝚒𝚘𝚗𝚂𝚒𝚣𝚎𝙴𝚕𝚎𝚖𝚎𝚗𝚝 using position size: {self.position_size} »"
