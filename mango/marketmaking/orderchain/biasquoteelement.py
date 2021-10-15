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


# # 🥭 BiasQuoteElement class
#
# Modifies an `Order`s price based. Uses `bias` to shift the price down to sell more (using
# a `biasquote-bias` of less than 1) or buy more (using a `biasquote-bias` of greater than 1).
#
class BiasQuoteElement(Element):
    def __init__(self, factor: Decimal):
        super().__init__()
        self.bias_factor: Decimal = factor

    @staticmethod
    def add_command_line_parameters(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--biasquote-factor", type=Decimal, default=Decimal(0),
                            help="bias factor to apply to quotes. Prices will be multiplied by this factor, so a number less than 1 will reduce prices and a number greater than 1 will increase prices. For example, use 1.001 to increase prices by 10 bips.")

    @staticmethod
    def from_command_line_parameters(args: argparse.Namespace) -> "BiasQuoteElement":
        return BiasQuoteElement(args.biasquote_factor or Decimal(1))

    def process(self, context: mango.Context, model_state: ModelState, orders: typing.Sequence[mango.Order]) -> typing.Sequence[mango.Order]:
        if self.bias_factor == 1:
            # Bias factor of 1 results in no changes to orders.
            return orders

        new_orders: typing.List[mango.Order] = []
        for order in orders:
            new_price: Decimal = order.price * self.bias_factor
            new_order: mango.Order = order.with_price(new_price)
            bias_description = "BUY more" if self.bias_factor > 1 else "SELL more"
            self.logger.debug(f"""Order change - bias factor {self.bias_factor} shifted price to {bias_description}:
    Old: {order}
    New: {new_order}""")
            new_orders += [new_order]

        return new_orders

    def __str__(self) -> str:
        return f"« 𝙱𝚒𝚊𝚜𝚀𝚞𝚘𝚝𝚎𝙴𝚕𝚎𝚖𝚎𝚗𝚝 - bias factor: {self.bias_factor} »"
