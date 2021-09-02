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
from ..modelstate import ModelState


# # 🥭 FixedRatiosDesiredOrdersBuilder class
#
# Ignores any input `Order`s (so probably best at the head of the chain). Builds orders using a fixed spread
# ratio and a fixed position size ratio.
#
class FixedRatiosElement(Element):
    def __init__(self, args: argparse.Namespace):
        super().__init__(args)
        self.spread_ratios: typing.Sequence[Decimal] = args.fixed_spread_ratio or []
        self.position_size_ratios: typing.Sequence[Decimal] = args.fixed_position_size_ratio or []
        self.order_type: mango.OrderType = args.order_type

        if len(self.spread_ratios) == 0:
            raise Exception("No spread ratios specified. Try the --fixed-spread-ratio parameter?")

        if len(self.position_size_ratios) == 0:
            raise Exception("No position-size ratios specified. Try the --fixed-position-size-ratio parameter?")

        if len(self.spread_ratios) != len(self.position_size_ratios):
            raise Exception("List of spread ratios and position size ratios must be the same length.")

    @staticmethod
    def add_command_line_parameters(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--fixed-spread-ratio", type=Decimal, action="append",
                            help="ratio to apply to the mid-price to create the BUY and SELL price (can be specified multiple times but every occurrance must have a matching --position-size-ratio occurrance)")
        parser.add_argument("--fixed-position-size-ratio", type=Decimal, action="append",
                            help="ratio to apply to the available collateral to create the position size (can be specified multiple times but every occurrance must have a matching --spread-ratio occurrance)")

    def process(self, context: mango.Context, model_state: ModelState, orders: typing.Sequence[mango.Order]) -> typing.Sequence[mango.Order]:
        price: mango.Price = model_state.price
        base_tokens: mango.TokenValue = model_state.inventory.base
        quote_tokens: mango.TokenValue = model_state.inventory.quote

        total = (base_tokens.value * price.mid_price) + quote_tokens.value

        new_orders: typing.List[mango.Order] = []
        for counter in range(len(self.spread_ratios)):
            position_size_ratio = self.position_size_ratios[counter]
            quote_value_to_risk = total * position_size_ratio
            base_position_size = quote_value_to_risk / price.mid_price

            spread_ratio = self.spread_ratios[counter]
            bid: Decimal = price.mid_price - (price.mid_price * spread_ratio)
            ask: Decimal = price.mid_price + (price.mid_price * spread_ratio)

            new_orders += [
                mango.Order.from_basic_info(mango.Side.BUY, price=bid,
                                            quantity=base_position_size, order_type=self.order_type),
                mango.Order.from_basic_info(mango.Side.SELL, price=ask,
                                            quantity=base_position_size, order_type=self.order_type)
            ]

        return new_orders

    def __str__(self) -> str:
        return f"« 𝙵𝚒𝚡𝚎𝚍𝚁𝚊𝚝𝚒𝚘𝚜𝙴𝚕𝚎𝚖𝚎𝚗𝚝 using ratios - spread: {self.spread_ratios}, position size: {self.position_size_ratios} »"
