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


# # 🥭 PreventPostOnlyCrossingBookElement class
#
# May modifiy an `Order`s price if it would result in too small a difference from the mid-price, meaning less
# of a charge if that `Order` is filled.
#
class PreventPostOnlyCrossingBookElement(Element):
    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def add_command_line_parameters(parser: argparse.ArgumentParser) -> None:
        pass

    @staticmethod
    def from_command_line_parameters(args: argparse.Namespace) -> "PreventPostOnlyCrossingBookElement":
        return PreventPostOnlyCrossingBookElement()

    def process(self, context: mango.Context, model_state: ModelState, orders: typing.Sequence[mango.Order]) -> typing.Sequence[mango.Order]:
        new_orders: typing.List[mango.Order] = []
        for order in orders:
            if order.order_type == mango.OrderType.POST_ONLY:
                top_bid: typing.Optional[Decimal] = model_state.top_bid.price if model_state.top_bid is not None else None
                top_ask: typing.Optional[Decimal] = model_state.top_ask.price if model_state.top_ask is not None else None
                if order.side == mango.Side.BUY and top_ask is not None and order.price >= top_ask:
                    new_buy_price: Decimal = top_ask - model_state.market.lot_size_converter.tick_size
                    new_buy: mango.Order = order.with_price(new_buy_price)
                    self._logger.debug(f"""Order change - would cross the orderbook {top_bid} / {top_ask}:
    Old: {order}
    New: {new_buy}""")
                    new_orders += [new_buy]
                elif order.side == mango.Side.SELL and top_bid is not None and order.price <= top_bid:
                    new_sell_price: Decimal = top_bid + model_state.market.lot_size_converter.tick_size
                    new_sell: mango.Order = order.with_price(new_sell_price)
                    self._logger.debug(
                        f"""Order change - would cross the orderbook {top_bid} / {top_ask}:
    Old: {order}
    New: {new_sell}""")

                    new_orders += [new_sell]
                else:
                    # All OK with current order
                    new_orders += [order]
            else:
                # Only change POST_ONLY orders.
                new_orders += [order]

        return new_orders

    def __str__(self) -> str:
        return "« PreventPostOnlyCrossingBookElement »"
