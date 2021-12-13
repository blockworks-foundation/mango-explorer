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


# # 🥭 FixedSpreadElement class
#
# Ignores any input `Order`s (so probably best at the head of the chain). Builds orders using a fixed spread
# value.
#
class FixedSpreadElement(PairwiseElement):
    def __init__(self, spreads: typing.Sequence[Decimal]) -> None:
        super().__init__()
        self.spreads: typing.Sequence[Decimal] = spreads

    @staticmethod
    def add_command_line_parameters(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--fixedspread-value", type=Decimal, action="append",
                            help="fixed value to apply to the mid-price to create the BUY and SELL price. Can be specified multiple times for multiple levels of BUYs and SELLs.")

    @staticmethod
    def from_command_line_parameters(args: argparse.Namespace) -> "FixedSpreadElement":
        if args.fixedspread_value is None:
            raise Exception("No spread value specified. Try the --fixedspread-value parameter?")

        spreads: typing.Sequence[Decimal] = args.fixedspread_value
        return FixedSpreadElement(spreads)

    def process_order_pair(self, context: mango.Context, model_state: ModelState, index: int, buy: typing.Optional[mango.Order], sell: typing.Optional[mango.Order]) -> typing.Tuple[typing.Optional[mango.Order], typing.Optional[mango.Order]]:
        # If no spread is explicitly specified for this element, just use the last specified spread.
        spread: Decimal = self.spreads[index] if index < len(self.spreads) else self.spreads[-1]
        half_spread: Decimal = spread / 2
        price: mango.Price = model_state.price
        new_buy: typing.Optional[mango.Order] = None
        new_sell: typing.Optional[mango.Order] = None
        if buy is not None:
            new_buy_price: Decimal = price.mid_price - half_spread
            new_buy = buy.with_price(new_buy_price)
            self._logger.debug(f"""Order change - using fixed spread of {spread:,.8f} - new BUY price {new_buy_price:,.8f} is {half_spread:,.8f} from mid price {price.mid_price:,.8f}:
    Old: {buy}
    New: {new_buy}""")

        if sell is not None:
            new_sell_price: Decimal = price.mid_price + half_spread
            new_sell = sell.with_price(new_sell_price)
            self._logger.debug(f"""Order change - using fixed spread of {spread:,.8f} - new SELL price {new_sell_price:,.8f} is {half_spread:,.8f} from mid price {price.mid_price:,.8f}:
    Old: {sell}
    New: {new_sell}""")

        return new_buy, new_sell

    def __str__(self) -> str:
        return f"« FixedSpreadElement using spreads {self.spreads} »"
