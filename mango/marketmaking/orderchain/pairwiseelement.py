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

import abc
import mango
import typing

from .element import Element
from ...modelstate import ModelState


# # 🥭 PairwiseElement class
#
# Some `Element`s want to process `Order`s in pairs or levels. Typically they'll have a BUY and a
# SELL at one spread, another BUY and SELL at a second spread, another BUY and SELL at a third
# spread, and so on.
#
# The 'desired orders' that come in don't fit that pattern though. It's just a list of `Order`s.
# The `Order`s may have a pair-wise structure, but it's not imposed upon them.
#
# If the `Order`s _do_ have such a pair-wise structure, some `Element`s can take advantage of that.
#
# (The assumption is that if your `Order`s _don't_ have a pair-wise structure - a matching BUY for
# each SELL - then you don't expect to successfully use `Element`s that depend upon such a
# structure.)
#
# The `PairwiseElement` handles converting from an unstructured list of `Order`s into a pair-wise
# structure, and then calls the derived class's `process_order_pair()` method to process a pair.
#
class PairwiseElement(Element, metaclass=abc.ABCMeta):
    def __init__(self) -> None:
        super().__init__()

    def process_order_pair(self, context: mango.Context, model_state: ModelState, index: int, buy: typing.Optional[mango.Order], sell: typing.Optional[mango.Order]) -> typing.Tuple[typing.Optional[mango.Order], typing.Optional[mango.Order]]:
        raise NotImplementedError("PairwiseElement.process_order_pair() is not implemented on the base type.")

    # If multiple levels are specified, we want to process them in order.
    #
    # But 'in order' is complicated. The way it will be expected to work is:
    # * First BUY and first SELL are treated as a pair
    # * Second BUY and second SELL are treated as a pair
    # * Third BUY and third SELL are treated as a pair
    # * etc.
    # But (another but!) 'first' means closest to the top of the book to people, not necessarily
    # first in the incoming order list.
    #
    # We want to meet that expected approach, so we'll:
    # * Split the list into BUYs and SELLs
    # * Sort the two lists so closest to top-of-book is at index 0
    # * Call process_order_pair() for each paired BUY and SELL, with the index parameter being
    #   the index into the BUY and SELL lists.
    def process(self, context: mango.Context, model_state: ModelState, orders: typing.Sequence[mango.Order]) -> typing.Sequence[mango.Order]:
        buys: typing.List[mango.Order] = list([order for order in orders if order.side == mango.Side.BUY])
        buys.sort(key=lambda order: order.price, reverse=True)
        sells: typing.List[mango.Order] = list([order for order in orders if order.side == mango.Side.SELL])
        sells.sort(key=lambda order: order.price)

        pair_count: int = max(len(buys), len(sells))
        new_orders: typing.List[mango.Order] = []
        for index in range(pair_count):
            old_buy: typing.Optional[mango.Order] = buys[index] if index < len(buys) else None
            old_sell: typing.Optional[mango.Order] = sells[index] if index < len(sells) else None

            (new_buy, new_sell) = self.process_order_pair(context, model_state, index, old_buy, old_sell)
            if new_buy is not None:
                new_orders += [new_buy]

            if new_sell is not None:
                new_orders += [new_sell]

        return new_orders

    def __str__(self) -> str:
        return "« PairwiseElement »"
