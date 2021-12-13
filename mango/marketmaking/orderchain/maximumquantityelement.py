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


# # 🥭 MaximumQuantityElement class
#
# Ensures orders' quantities are always less than the maximum. Will either:
# * Remove the order if the position size is too high, or
# * Set the too-high position size to the permitted maximum
#
class MaximumQuantityElement(Element):
    def __init__(self, maximum_quantity: Decimal, remove: bool = False) -> None:
        super().__init__()
        self.maximum_quantity: Decimal = maximum_quantity
        self.remove: bool = remove

    @staticmethod
    def add_command_line_parameters(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--maximumquantity-size", type=Decimal,
                            help="the maximum permitted order quantity")
        parser.add_argument("--maximumquantity-remove", action="store_true", default=False,
                            help="remove an order that has too big a quantity (default is to reduce order quantity to maximum)")

    @staticmethod
    def from_command_line_parameters(args: argparse.Namespace) -> "MaximumQuantityElement":
        if args.maximumquantity_size is None:
            raise Exception("No maximum size specified. Try the --maximumquantity-size parameter?")

        return MaximumQuantityElement(args.maximumquantity_size, bool(args.maximumquantity_remove))

    def process(self, context: mango.Context, model_state: ModelState, orders: typing.Sequence[mango.Order]) -> typing.Sequence[mango.Order]:
        new_orders: typing.List[mango.Order] = []
        for order in orders:
            if order.quantity < self.maximum_quantity:
                new_orders += [order]
            else:
                if self.remove:
                    self._logger.debug(f"""Order change - order quantity is greater than maximum of {self.maximum_quantity} so removing:
    Old: {order}
    New: None""")
                else:
                    new_order: mango.Order = order.with_quantity(self.maximum_quantity)
                    self._logger.debug(f"""Order change - order quantity is greater than maximum of {self.maximum_quantity} so changing order quantity to {self.maximum_quantity}:
    Old: {order}
    New: {new_order}""")
                    new_orders += [new_order]

        return new_orders

    def __str__(self) -> str:
        return f"« MaximumQuantityElement [maximum quantity: {self.maximum_quantity}, remove: {self.remove}] »"
