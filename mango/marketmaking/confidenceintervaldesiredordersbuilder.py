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

from .desiredordersbuilder import DesiredOrdersBuilder
from .modelstate import ModelState


# # 🥭 ConfidenceIntervalDesiredOrdersBuilder class
#
# Builds orders using a fixed position size ratio but with a spread based on the confidence in the oracle price.
#
class ConfidenceIntervalDesiredOrdersBuilder(DesiredOrdersBuilder):
    def __init__(self, position_size_ratio: Decimal, min_price_ratio: Decimal, confidence_interval_levels: typing.Sequence[Decimal] = [Decimal(2)], order_type: mango.OrderType = mango.OrderType.POST_ONLY, quote_position_bias: Decimal = Decimal(0)):
        super().__init__()
        self.position_size_ratio: Decimal = position_size_ratio
        self.min_price_ratio: Decimal = min_price_ratio
        self.confidence_interval_levels: typing.Sequence[Decimal] = confidence_interval_levels
        self.order_type: mango.OrderType = order_type
        self.quote_position_bias: Decimal = quote_position_bias

    def build(self, context: mango.Context, model_state: ModelState) -> typing.Sequence[mango.Order]:
        price: mango.Price = model_state.price
        if price.source.supports & mango.SupportedOracleFeature.CONFIDENCE == 0:
            raise Exception(f"Price does not support confidence interval: {price}")

        base_tokens: mango.TokenValue = model_state.inventory.base
        quote_tokens: mango.TokenValue = model_state.inventory.quote

        total = (base_tokens.value * price.mid_price) + quote_tokens.value
        quote_value_to_risk = total * self.position_size_ratio
        position_size = quote_value_to_risk / price.mid_price

        orders: typing.List[mango.Order] = []

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
        bias = (1 + (model_state.inventory.base.value / position_size) * quote_position_bias)

        for confidence_interval_level in self.confidence_interval_levels:
            # From Daffy on 26th July 2021: max(pyth_conf * 2, price * min_charge)
            # (Private chat link: https://discord.com/channels/@me/832570058861314048/869208592648134666)
            charge = max(price.confidence * confidence_interval_level, price.mid_price * self.min_price_ratio)
            bid: Decimal = (price.mid_price - charge) * bias
            ask: Decimal = (price.mid_price + charge) * bias

            orders += [
                mango.Order.from_basic_info(mango.Side.BUY, price=bid,
                                            quantity=position_size, order_type=self.order_type),
                mango.Order.from_basic_info(mango.Side.SELL, price=ask,
                                            quantity=position_size, order_type=self.order_type)
            ]

        return orders

    def __str__(self) -> str:
        return f"« 𝙲𝚘𝚗𝚏𝚒𝚍𝚎𝚗𝚌𝚎𝙸𝚗𝚝𝚎𝚛𝚟𝚊𝚕𝙳𝚎𝚜𝚒𝚛𝚎𝚍𝙾𝚛𝚍𝚎𝚛𝚜𝙱𝚞𝚒𝚕𝚍𝚎𝚛 {self.order_type} - position size: {self.position_size_ratio}, min charge: {self.min_price_ratio}, confidence interval levels: {self.confidence_interval_levels} »"
