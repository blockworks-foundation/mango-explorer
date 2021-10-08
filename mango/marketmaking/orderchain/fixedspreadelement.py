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


# # 🥭 FixedSpreadElement class
#
# Ignores any input `Order`s (so probably best at the head of the chain). Builds orders using a fixed spread
# value.
#
class FixedSpreadElement(Element):
    def __init__(self, spread: Decimal):
        super().__init__()
        self.half_spread: Decimal = spread / 2

    @staticmethod
    def add_command_line_parameters(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--fixedspread-value", type=Decimal,
                            help="fixed value to apply to the mid-price to create the BUY and SELL price (only works well with a single 'level' of orders - one BUY and one SELL)")

    @staticmethod
    def from_command_line_parameters(args: argparse.Namespace) -> "FixedSpreadElement":
        if args.fixedspread_value is None:
            raise Exception("No spread value specified. Try the --fixedspread-value parameter?")

        spread: Decimal = args.fixedspread_value
        return FixedSpreadElement(spread)

    def process(self, context: mango.Context, model_state: ModelState, orders: typing.Sequence[mango.Order]) -> typing.Sequence[mango.Order]:
        price: mango.Price = model_state.price
        new_orders: typing.List[mango.Order] = []
        for order in orders:
            new_price: Decimal = price.mid_price - self.half_spread if order.side == mango.Side.BUY else price.mid_price + self.half_spread
            new_order: mango.Order = order.with_price(new_price)

            self.logger.debug(f"""Order change - using fixed spread of {self.half_spread * 2}:
    Old: {order}
    New: {new_order}""")
            new_orders += [new_order]

        return new_orders

    def __str__(self) -> str:
        return f"« 𝙵𝚒𝚡𝚎𝚍𝚂𝚙𝚛𝚎𝚊𝚍𝙴𝚕𝚎𝚖𝚎𝚗𝚝 using spread value {self.half_spread * 2} »"
