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
from solana.publickey import PublicKey

from .element import Element
from ...modelstate import ModelState


# # 🥭 TopOfBookElement class
#
# Shifts orders so they're always at the top of the book - 1 tick above/below anyone else's top-of-book.
#
# Looks at the top order on the orderbook that isn't owned by the current account. Then places the desired
# order at 1 tick better than that top order. ('1 tick' here can be tweaked by the `adjustment_ticks`
# parameter.)
#
# Probably works best with POST_ONLY_SLIDE in case the spread is zero.
#
class TopOfBookElement(Element):
    def __init__(self, adjustment_ticks: Decimal = Decimal(1)) -> None:
        super().__init__()
        self.adjustment_ticks: Decimal = adjustment_ticks

    @staticmethod
    def add_command_line_parameters(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--topofbook-adjustment-ticks", type=Decimal, default=Decimal(1),
                            help="number of ticks above/below the previous top-of-book to place the order. Default is 1 tick  - 1 tick below for a SELL, 1 tick above for a BUY. Use 0 to specify placing the order AT the current best.")

    @staticmethod
    def from_command_line_parameters(args: argparse.Namespace) -> "TopOfBookElement":
        return TopOfBookElement(args.topofbook_adjustment_ticks)

    def _best_order_from_someone_else(self, orders: typing.Sequence[mango.Order], owner: PublicKey) -> typing.Optional[mango.Order]:
        for order in orders:
            if order.owner != owner:
                # Success!
                return order
        return None

    def process(self, context: mango.Context, model_state: ModelState, orders: typing.Sequence[mango.Order]) -> typing.Sequence[mango.Order]:
        new_orders: typing.List[mango.Order] = []
        adjustment: Decimal = self.adjustment_ticks * model_state.market.lot_size_converter.tick_size
        for order in orders:
            new_price: typing.Optional[Decimal] = None
            if order.side == mango.Side.BUY:
                place_above: typing.Optional[mango.Order] = self._best_order_from_someone_else(
                    model_state.bids, model_state.order_owner)
                if place_above is not None:
                    new_price = place_above.price + adjustment
            else:
                place_below: typing.Optional[mango.Order] = self._best_order_from_someone_else(
                    model_state.asks, model_state.order_owner)
                if place_below is not None:
                    new_price = place_below.price - adjustment

            if new_price is None:
                self._logger.debug(f"""Order change - no acceptable price from anyone else so leaving it as it is:
    Old: {order}
    New: {order}""")
                new_orders += [order]
            else:
                new_order: mango.Order = order.with_price(new_price)
                self._logger.debug(f"""Order change - top of book from others is {self.adjustment_ticks} tick from {new_price}:
    Old: {order}
    New: {new_order}""")
                new_orders += [new_order]

        return new_orders

    def __str__(self) -> str:
        return f"« 𝚃𝚘𝚙𝙾𝚏𝙱𝚘𝚘𝚔𝙴𝚕𝚎𝚖𝚎𝚗𝚝 [adjustment ticks: {self.adjustment_ticks}] »"
