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


import logging
import mango
import typing

from .element import Element
from ...modelstate import ModelState


# # 🥭 Chain class
#
# A `Chain` object takes a series of `Element`s and calls them in sequence to build a list of
# desired `Order`s.
#
# Only `Order`s returned from `process()` method are used as the final list of 'desired orders' for
# reconciling and possibly adding to the orderbook.
#
class Chain:
    def __init__(self, elements: typing.Sequence[Element]) -> None:
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.elements: typing.Sequence[Element] = elements

    def process(self, context: mango.Context, model_state: ModelState) -> typing.Sequence[mango.Order]:
        orders: typing.Sequence[mango.Order] = []
        for element in self.elements:
            orders = element.process(context, model_state, orders)
        return orders

    def __repr__(self) -> str:
        return f"{self}"

    def __str__(self) -> str:
        elements = "\n    ".join(map(str, self.elements)) or "None"

        return f"""« Chain of {len(self.elements)} elements:
    {elements}
»"""
