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


import mango
import typing

from decimal import Decimal

from .element import Element
from ..modelstate import ModelState


# # 🥭 BiasQuoteOnPositionElement class
#
# Modifies an `Order`s price based on current inventory. Uses `quote_position_bias` to shift the price to sell
# more (if too much inventory) or buy more (if too little inventory).
#
class BiasQuoteOnPositionElement(Element):
    def __init__(self, quote_position_bias: Decimal = Decimal(0)):
        super().__init__()
        self.quote_position_bias: Decimal = quote_position_bias

    def process(self, context: mango.Context, model_state: ModelState, orders: typing.Sequence[mango.Order]) -> typing.Sequence[mango.Order]:
        if self.quote_position_bias == 0:
            # Zero bias results in no changes to orders.
            return orders

        # From Daffy on 20th August 2021:
        #  Formula to adjust price might look like this `pyth_price * (1 + (curr_pos / size) * pos_lean)`
        #  where pos_lean is a negative number
        #
        #  size is the standard size you're quoting which I believe comes from the position-size-ratio
        #
        #  So if my standard size I'm quoting is 0.0002 BTC, my current position is +0.0010 BTC, and pos_lean
        #  is -0.0001, you would move your quotes down by 0.0005 (or 5bps)
        # (Private chat link: https://discord.com/channels/@me/832570058861314048/878343278523723787)
        quote_position_bias = self.quote_position_bias * -1
        new_orders: typing.List[mango.Order] = []
        for order in orders:
            bias = (1 + (model_state.inventory.base.value / order.quantity) * quote_position_bias)
            new_price: Decimal = order.price * bias
            new_order: mango.Order = order.with_price(new_price)
            bias_description = "BUY more" if bias > 0 else "SELL more"
            self.logger.debug(f"""Order change - quote_position_bias {self.quote_position_bias} creates a ({bias_description}) bias factor of {bias}:
    Old: {order}
    New: {new_order}""")
            new_orders += [new_order]

        return new_orders

    def __str__(self) -> str:
        return f"« 𝙱𝚒𝚊𝚜𝚀𝚞𝚘𝚝𝚎𝙾𝚗𝙿𝚘𝚜𝚒𝚝𝚒𝚘𝚗𝙴𝚕𝚎𝚖𝚎𝚗𝚝 - bias: {self.quote_position_bias} »"
