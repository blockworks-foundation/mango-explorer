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


# # 🥭 BiasQuantityOnPositionElement class
#
# Modifies an `Order`s quantity based on current inventory. Looks at the current position, the maximum desired
# position, and the target position. Tries to bias the order quantity to tend towards the target position,
# incresing the order quantities that shift it in that direction and decreasing the order quantities that
# shift it away from the target.
#
# For example(1):
#  BUY quantity: 10
#  SELL quantity: 10
#  CURRENT position: 0
#  MAXIMUM position: 50
#  TARGET position: 0
#  Result: no change
#
# For example(2):
#  BUY quantity: 10
#  SELL quantity: 10
#  CURRENT position: 20
#  MAXIMUM position: 50
#  TARGET position: 0
#  Result:
#    BUY quantity: 6
#    SELL quantity: 14
#
# In example (2) you can see:
# * the current position of 20 means BUY quantity has decreased and SELL quantity has increased
# * the total quantity in BUY and SELL stays the same, at 20
#
# More examples (including all data used in unit tests) are available in the
# docs/BiasQuantityOnPosition.ods spreadsheet.
#
class BiasQuantityOnPositionElement(PairwiseElement):
    def __init__(self, maximum_position: Decimal, target_position: Decimal = Decimal(0)) -> None:
        super().__init__()
        self.maximum_position: Decimal = maximum_position
        self.target_position: Decimal = target_position

    @staticmethod
    def add_command_line_parameters(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--biasquantityonposition-maximum-position", type=Decimal,
                            help="maximum inventory position to proportionally move away from")
        parser.add_argument("--biasquantityonposition-target-position", type=Decimal,
                            help="inventory position to target (default 0)")

    @staticmethod
    def from_command_line_parameters(args: argparse.Namespace) -> "BiasQuantityOnPositionElement":
        if args.biasquantityonposition_maximum_position is None:
            raise Exception(
                "No maximum position value specified for biasing. Try the --biasquantityonposition-maximum-position parameter?")
        maximum_position: Decimal = args.biasquantityonposition_maximum_position
        target_position: Decimal = args.biasquantityonposition_target_position or Decimal(0)
        return BiasQuantityOnPositionElement(maximum_position, target_position)

    def process_order_pair(self, context: mango.Context, model_state: ModelState, index: int, buy: typing.Optional[mango.Order], sell: typing.Optional[mango.Order]) -> typing.Tuple[typing.Optional[mango.Order], typing.Optional[mango.Order]]:
        if buy is not None and sell is not None:
            total_quantity = buy.quantity + sell.quantity
            current_position = model_state.inventory.base.value

            # BUY adjustment formula from the spreadsheet:
            #   =MIN((A2+B2), MAX(0, ((D2-(C2-E2))/D2)*A2))
            biased_buy_quantity = ((self.maximum_position - (current_position - self.target_position)
                                    ) / self.maximum_position) * buy.quantity
            clamped_biased_buy_quantity = min(total_quantity, max(Decimal(0), biased_buy_quantity))
            if buy.quantity != clamped_biased_buy_quantity:
                new_buy = buy.with_quantity(clamped_biased_buy_quantity)
                buy_bias_description = "BUY more" if clamped_biased_buy_quantity > buy.quantity else "BUY less"
                self._logger.debug(f"""BUY order change - maximum position {self.maximum_position} with current position {current_position} and target position {self.target_position} creates a {buy_bias_description} bias:
    Old: {buy}
    New: {new_buy}""")
                buy = new_buy

            # SELL adjustment formula from the spreadsheet:
            #   =MIN((A2+B2), MAX(0, (2-((D2-(C2-E2))/D2))*B2))
            biased_sell_quantity = (2 - ((self.maximum_position - (current_position - self.target_position)
                                          ) / self.maximum_position)) * sell.quantity
            clamped_biased_sell_quantity = min(total_quantity, max(Decimal(0), biased_sell_quantity))
            if sell.quantity != clamped_biased_sell_quantity:
                new_sell = sell.with_quantity(clamped_biased_sell_quantity)
                sell_bias_description = "SELL more" if clamped_biased_sell_quantity > sell.quantity else "SELL less"
                self._logger.debug(f"""SELL order change - maximum position {self.maximum_position} with current position {current_position} and target position {self.target_position} creates a {sell_bias_description} bias:
    Old: {sell}
    New: {new_sell}""")
                sell = new_sell

        return buy, sell

    def __str__(self) -> str:
        return f"« BiasQuantityOnPositionElement - maximum: {self.maximum_position}, target: {self.target_position} »"
