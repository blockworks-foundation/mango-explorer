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

from .element import Element
from ...modelstate import ModelState


# # 🥭 QuoteSingleSideElement class
#
# Only allows orders from one side of the book to progress to the next element of the chain.
#
class QuoteSingleSideElement(Element):
    def __init__(self, side: mango.Side):
        super().__init__()
        self.allowed: mango.Side = side

    @staticmethod
    def add_command_line_parameters(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--quotesingleside-side", type=mango.Side,
                            help="the single side to quote on - if BUY, all SELLs will be removed from desired orders, if SELL, all BUYs will be removed.")

    @staticmethod
    def from_command_line_parameters(args: argparse.Namespace) -> "QuoteSingleSideElement":
        side: mango.Side = args.quotesingleside_side
        return QuoteSingleSideElement(side)

    def process(self, context: mango.Context, model_state: ModelState, orders: typing.Sequence[mango.Order]) -> typing.Sequence[mango.Order]:
        new_orders: typing.List[mango.Order] = []
        for order in orders:
            if order.side == self.allowed:
                self.logger.debug(f"""Allowing {order.side} order [allowed: {self.allowed}]:
    Allowed: {order}""")
                new_orders += [order]
            else:
                self.logger.debug(f"""Removing {order.side} order [allowed: {self.allowed}]:
    Removed: {order}""")

        return new_orders

    def __str__(self) -> str:
        return "« 𝚀𝚞𝚘𝚝𝚎𝚂𝚒𝚗𝚐𝚕𝚎𝚂𝚒𝚍𝚎𝙴𝚕𝚎𝚖𝚎𝚗𝚝 »"
