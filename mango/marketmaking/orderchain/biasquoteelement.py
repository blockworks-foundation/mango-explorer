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


# # 🥭 BiasQuoteElement class
#
# Modifies an `Order`s price based. Uses `bias` to shift the price down to sell more (using
# a `biasquote-bias` of less than 1) or buy more (using a `biasquote-bias` of greater than 1).
#
# Can take multiple bias factors to work with pair-wise orders.
#
class BiasQuoteElement(PairwiseElement):
    def __init__(self, factors: typing.Sequence[Decimal]) -> None:
        super().__init__()
        self.bias_factors: typing.Sequence[Decimal] = factors

    @staticmethod
    def add_command_line_parameters(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--biasquote-factor", type=Decimal, action="append",
                            help="bias factor to apply to quotes. Prices will be multiplied by this factor, so a number less than 1 will reduce prices and a number greater than 1 will increase prices. For example, use 1.001 to increase prices by 10 bips. Can be specified multiple times to apply to different levels.")

    @staticmethod
    def from_command_line_parameters(args: argparse.Namespace) -> "BiasQuoteElement":
        bias_factors: typing.Sequence[Decimal] = args.biasquote_factor
        return BiasQuoteElement(bias_factors or [Decimal(1)])

    def process_order_pair(self, context: mango.Context, model_state: ModelState, index: int, buy: typing.Optional[mango.Order], sell: typing.Optional[mango.Order]) -> typing.Tuple[typing.Optional[mango.Order], typing.Optional[mango.Order]]:
        # If no bias is explicitly specified for this element, just use the last specified bias.
        bias_factor: Decimal = self.bias_factors[index] if index < len(self.bias_factors) else self.bias_factors[-1]
        bias_description = "BUY more" if bias_factor > 1 else "SELL more"

        if bias_factor == 1:
            # Bias factor of 1 results in no changes to orders.
            return buy, sell

        new_buy: typing.Optional[mango.Order] = None
        new_sell: typing.Optional[mango.Order] = None
        if buy is not None:
            new_buy_price: Decimal = buy.price * bias_factor
            new_buy = buy.with_price(new_buy_price)
            self._logger.debug(f"""Order change - bias factor of {bias_factor} shifted price to {bias_description}:
    Old: {buy}
    New: {new_buy}""")

        if sell is not None:
            new_sell_price: Decimal = sell.price * bias_factor
            new_sell = sell.with_price(new_sell_price)
            self._logger.debug(f"""Order change - bias factor of {bias_factor} shifted price to {bias_description}:
    Old: {sell}
    New: {new_sell}""")

        return new_buy, new_sell

    def __str__(self) -> str:
        return f"« BiasQuoteElement - bias factors: {self.bias_factors} »"
