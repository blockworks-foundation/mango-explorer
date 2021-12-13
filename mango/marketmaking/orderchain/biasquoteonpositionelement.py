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


# # 🥭 BiasQuoteOnPositionElement class
#
# Modifies an `Order`s price based on current inventory. Uses a `bias` to shift the price to sell
# more (if too much inventory) or buy more (if too little inventory).
#
# Can take multiple bias factors to work with pair-wise orders.
#
class BiasQuoteOnPositionElement(PairwiseElement):
    def __init__(self, biases: typing.Sequence[Decimal]) -> None:
        super().__init__()
        self.biases: typing.Sequence[Decimal] = biases

    @staticmethod
    def add_command_line_parameters(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--biasquoteonposition-bias", type=Decimal, action="append",
                            help="bias to apply to quotes based on inventory position")

    @staticmethod
    def from_command_line_parameters(args: argparse.Namespace) -> "BiasQuoteOnPositionElement":
        biases: typing.Sequence[Decimal] = args.biasquoteonposition_bias or [Decimal(0)]
        return BiasQuoteOnPositionElement(biases)

    def process_order_pair(self, context: mango.Context, model_state: ModelState, index: int, buy: typing.Optional[mango.Order], sell: typing.Optional[mango.Order]) -> typing.Tuple[typing.Optional[mango.Order], typing.Optional[mango.Order]]:
        # If no bias is explicitly specified for this element, just use the last specified bias.
        bias: Decimal = self.biases[index] if index < len(self.biases) else self.biases[-1]
        if bias == 0:
            # Zero bias results in no changes to orders.
            return buy, sell

        new_buy: typing.Optional[mango.Order] = None
        new_sell: typing.Optional[mango.Order] = None
        if buy is not None:
            new_buy = self.bias_order(buy, bias, model_state.inventory.base.value)

        if sell is not None:
            new_sell = self.bias_order(sell, bias, model_state.inventory.base.value)

        return new_buy, new_sell

    # From Daffy on 20th August 2021:
    #  Formula to adjust price might look like this `pyth_price * (1 + (curr_pos / size) * pos_lean)`
    #  where pos_lean is a negative number
    #
    #  size is the standard size you're quoting which I believe comes from the position-size-ratio
    #
    #  So if my standard size I'm quoting is 0.0002 BTC, my current position is +0.0010 BTC, and pos_lean
    #  is -0.0001, you would move your quotes down by 0.0005 (or 5bps)
    # (Private chat link: https://discord.com/channels/@me/832570058861314048/878343278523723787)
    def bias_order(self, order: mango.Order, inventory_bias: Decimal, base_inventory_value: Decimal) -> mango.Order:
        bias_factor = inventory_bias * -1
        bias = 1 + ((base_inventory_value / order.quantity) * bias_factor)
        new_price: Decimal = order.price * bias
        new_order: mango.Order = order.with_price(new_price)
        bias_description = "BUY more" if bias > 1 else "SELL more"
        self._logger.debug(f"""Order change - bias {inventory_bias} on inventory {base_inventory_value} / {order.quantity} creates a ({bias_description}) bias factor of {bias}:
    Old: {order}
    New: {new_order}""")
        return new_order

    def __str__(self) -> str:
        return f"« BiasQuoteOnPositionElement - biases: {self.biases} »"
