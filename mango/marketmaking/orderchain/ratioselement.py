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


DEFAULT_SPREAD_RATIO = Decimal("0.01")
DEFAULT_POSITION_SIZE_RATIO = Decimal("0.01")


# # 🥭 RatiosElement class
#
# Ignores any input `Order`s (so probably best at the head of the chain). Builds orders using a spread
# ratio and a position size ratio.
#
class RatiosElement(Element):
    def __init__(self, order_type: mango.OrderType, spread_ratios: typing.Sequence[Decimal], position_size_ratios: typing.Sequence[Decimal], from_bid_ask: bool) -> None:
        super().__init__()
        self.order_type: mango.OrderType = order_type
        self.spread_ratios: typing.Sequence[Decimal] = spread_ratios
        self.position_size_ratios: typing.Sequence[Decimal] = position_size_ratios
        self.from_bid_ask: bool = from_bid_ask

        if len(self.spread_ratios) == 0:
            raise Exception("No spread ratios specified. Try the --ratios-spread parameter?")

        if len(self.position_size_ratios) == 0:
            raise Exception("No position-size ratios specified. Try the --ratios-position-size parameter?")

        if len(self.spread_ratios) != len(self.position_size_ratios):
            raise Exception("List of spread ratios and position size ratios must be the same length.")

    @staticmethod
    def add_command_line_parameters(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--ratios-spread", type=Decimal, action="append",
                            help="ratio to apply to the mid-price to create the BUY and SELL price (can be specified multiple times but every occurrance must have a matching --position-size-ratio occurrance)")
        parser.add_argument("--ratios-position-size", type=Decimal, action="append",
                            help="ratio to apply to the available collateral to create the position size (can be specified multiple times but every occurrance must have a matching --spread-ratio occurrance)")
        parser.add_argument("--ratios-from-bid-ask", action="store_true", default=False,
                            help="calculate ratios from bid or ask, not mid price (default: False, which will use the mid price)")

    @staticmethod
    def from_command_line_parameters(args: argparse.Namespace) -> "RatiosElement":
        order_type: mango.OrderType = args.order_type
        spread_ratios: typing.Sequence[Decimal] = args.ratios_spread or [DEFAULT_SPREAD_RATIO]
        position_size_ratios: typing.Sequence[Decimal] = args.ratios_position_size or [DEFAULT_POSITION_SIZE_RATIO]
        from_bid_ask: bool = args.ratios_from_bid_ask
        return RatiosElement(order_type, spread_ratios, position_size_ratios, from_bid_ask)

    def process(self, context: mango.Context, model_state: ModelState, orders: typing.Sequence[mango.Order]) -> typing.Sequence[mango.Order]:
        price: mango.Price = model_state.price
        new_orders: typing.List[mango.Order] = []
        for counter in range(len(self.spread_ratios)):
            position_size_ratio = self.position_size_ratios[counter]
            quote_value_to_risk = model_state.inventory.available_collateral.value * position_size_ratio
            base_position_size = quote_value_to_risk / price.mid_price

            spread_ratio = self.spread_ratios[counter]
            bid_price_base: Decimal = price.mid_price
            ask_price_base: Decimal = price.mid_price
            if self.from_bid_ask:
                bid_price_base = price.top_bid
                ask_price_base = price.top_ask

            bid: Decimal = bid_price_base - (bid_price_base * spread_ratio)
            ask: Decimal = ask_price_base + (ask_price_base * spread_ratio)

            bid_order = mango.Order.from_basic_info(mango.Side.BUY, price=bid,
                                                    quantity=base_position_size, order_type=self.order_type)
            ask_order = mango.Order.from_basic_info(mango.Side.SELL, price=ask,
                                                    quantity=base_position_size, order_type=self.order_type)
            self._logger.debug(f"""Desired orders:
    Bid: {bid_order}
    Ask: {ask_order}""")
            new_orders += [bid_order, ask_order]

        return new_orders

    def __str__(self) -> str:
        spread_ratios = ", ".join(map(str, self.spread_ratios)) or "None"
        position_size_ratios = ", ".join(map(str, self.position_size_ratios)) or "None"
        from_description = "from bid/ask" if self.from_bid_ask else "from mid price"
        return f"« 𝚁𝚊𝚝𝚒𝚘𝚜𝙴𝚕𝚎𝚖𝚎𝚗𝚝 using ratios - spread(s): {spread_ratios} {from_description}, position size(s): {position_size_ratios} »"
