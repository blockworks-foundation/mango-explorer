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


# # 🥭 RoundToLotSizeElement class
#
# May modifiy an `Order`s price or quantity to ensure it's exactly aligned to the market's lot sizes.
#
class RoundToLotSizeElement(Element):
    def __init__(self):
        super().__init__()

    @staticmethod
    def add_command_line_parameters(parser: argparse.ArgumentParser) -> None:
        pass

    @staticmethod
    def from_command_line_parameters(args: argparse.Namespace) -> "RoundToLotSizeElement":
        return RoundToLotSizeElement()

    def process(self, context: mango.Context, model_state: ModelState, orders: typing.Sequence[mango.Order]) -> typing.Sequence[mango.Order]:
        new_orders: typing.List[mango.Order] = []
        for order in orders:
            new_price: Decimal = model_state.market.lot_size_converter.round_quote(order.price)
            new_quantity: Decimal = model_state.market.lot_size_converter.round_base(order.quantity)
            new_order: mango.Order = order
            if (new_order.price != new_price) or (new_order.quantity != new_quantity):
                new_order = new_order.with_price(new_price).with_quantity(new_quantity)
                self.logger.debug(f"""Order change - price is now aligned to lot size:
    Old: {order}
    New: {new_order}""")

            new_orders += [new_order]

        return new_orders

    def __str__(self) -> str:
        return "« 𝚁𝚘𝚞𝚗𝚍𝚃𝚘𝙻𝚘𝚝𝚂𝚒𝚣𝚎𝙴𝚕𝚎𝚖𝚎𝚗𝚝 »"
