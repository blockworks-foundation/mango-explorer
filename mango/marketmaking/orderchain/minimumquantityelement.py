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


# # 🥭 MinimumQuantityElement class
#
# Ensures orders' quantities are always greater than the minimum. Will either:
# * Remove the order if the position size is too low, or
# * Set the too-low position size to the permitted minimum
#
class MinimumQuantityElement(Element):
    def __init__(self, minimum_quantity: Decimal, remove: bool = False) -> None:
        super().__init__()
        self.minimum_quantity: Decimal = minimum_quantity
        self.remove: bool = remove

    @staticmethod
    def add_command_line_parameters(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--minimumquantity-size", type=Decimal, default=Decimal(1),
                            help="the minimum permitted quantity")
        parser.add_argument("--minimumquantity-remove", action="store_true", default=False,
                            help="remove an order that has too small a quantity (default is to increase order quantity to minimum)")

    @staticmethod
    def from_command_line_parameters(args: argparse.Namespace) -> "MinimumQuantityElement":
        if args.minimumquantity_size is None:
            raise Exception("No minimum size specified. Try the --minimumquantity-size parameter?")

        return MinimumQuantityElement(args.minimumquantity_size, bool(args.minimumquantity_remove))

    def process(self, context: mango.Context, model_state: ModelState, orders: typing.Sequence[mango.Order]) -> typing.Sequence[mango.Order]:
        new_orders: typing.List[mango.Order] = []
        for order in orders:
            if order.quantity > self.minimum_quantity:
                new_orders += [order]
            else:
                if self.remove:
                    self._logger.debug(f"""Order change - order quantity is less than minimum of {self.minimum_quantity} so removing:
    Old: {order}
    New: None""")
                else:
                    new_order: mango.Order = order.with_quantity(self.minimum_quantity)
                    self._logger.debug(f"""Order change - order quantity is less than minimum of {self.minimum_quantity} so changing order quantity to {self.minimum_quantity}:
    Old: {order}
    New: {new_order}""")
                    new_orders += [new_order]

        return new_orders

    def __str__(self) -> str:
        return f"« MinimumQuantityElement [minimum quantity: {self.minimum_quantity}, remove: {self.remove}] »"
