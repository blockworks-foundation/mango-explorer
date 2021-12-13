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


# # 🥭 MinimumChargeElement class
#
# May modifiy an `Order`s price if it would result in too small a difference from the mid-price, meaning less
# of a charge if that `Order` is filled.
#
# Can take multiple minimum charges to work with pair-wise orders.
#
class MinimumChargeElement(PairwiseElement):
    def __init__(self, ratios: typing.Sequence[Decimal], from_bid_ask: bool) -> None:
        super().__init__()
        self.minimumcharge_ratios: typing.Sequence[Decimal] = ratios
        self.minimumcharge_from_bid_ask: bool = from_bid_ask

    @staticmethod
    def add_command_line_parameters(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--minimumcharge-ratio", type=Decimal, action="append",
                            help="minimum fraction of the price to be accept as a spread")
        parser.add_argument("--minimumcharge-from-bid-ask", action="store_true", default=False,
                            help="calculate minimum charge from bid or ask, not mid price (default: False, which will use the mid price)")

    @staticmethod
    def from_command_line_parameters(args: argparse.Namespace) -> "MinimumChargeElement":
        minimumcharge_ratios: typing.Sequence[Decimal] = args.minimumcharge_ratio or [Decimal("0.0005")]
        minimumcharge_from_bid_ask: bool = args.minimumcharge_from_bid_ask
        return MinimumChargeElement(minimumcharge_ratios, minimumcharge_from_bid_ask)

    def process_order_pair(self, context: mango.Context, model_state: ModelState, index: int, buy: typing.Optional[mango.Order], sell: typing.Optional[mango.Order]) -> typing.Tuple[typing.Optional[mango.Order], typing.Optional[mango.Order]]:
        # If no bias is explicitly specified for this element, just use the last specified bias.
        minimum_charge_ratio: Decimal = self.minimumcharge_ratios[index] if index < len(
            self.minimumcharge_ratios) else self.minimumcharge_ratios[-1]
        if minimum_charge_ratio == 0:
            # Zero minimum charge results in no changes to orders.
            return buy, sell

        # From Daffy on 26th July 2021: max(pyth_conf * 2, price * min_charge)
        # (Private chat link: https://discord.com/channels/@me/832570058861314048/869208592648134666)
        new_buy: typing.Optional[mango.Order] = buy
        new_sell: typing.Optional[mango.Order] = sell
        measurement_price: Decimal
        minimum_charge: Decimal
        current_charge: Decimal
        new_price: Decimal
        if buy is not None:
            measurement_price = model_state.price.top_bid if self.minimumcharge_from_bid_ask else model_state.price.mid_price
            minimum_charge = measurement_price * minimum_charge_ratio
            current_charge = measurement_price - buy.price
            if current_charge < minimum_charge:
                new_price = measurement_price - minimum_charge
                new_buy = buy.with_price(new_price)
                self._logger.debug(f"""Order change - old BUY price {buy.price:,.8f} distance from {measurement_price:,.8f} would return {current_charge:,.8f} which is less than minimum charge {minimum_charge:,.8f}:
    Old: {buy}
    New: {new_buy}""")

        if sell is not None:
            measurement_price = model_state.price.top_ask if self.minimumcharge_from_bid_ask else model_state.price.mid_price
            minimum_charge = measurement_price * minimum_charge_ratio
            current_charge = sell.price - measurement_price
            if current_charge < minimum_charge:
                new_price = measurement_price + minimum_charge
                new_sell = sell.with_price(new_price)
                self._logger.debug(f"""Order change - old SELL price {sell.price:,.8f} distance from {measurement_price:,.8f} would return {current_charge:,.8f} which is less than minimum charge {minimum_charge:,.8f}:
    Old: {sell}
    New: {new_sell}""")

        return new_buy, new_sell

    def __str__(self) -> str:
        return f"« MinimumChargeElement - minimum charge ratios: {self.minimumcharge_ratios} »"
