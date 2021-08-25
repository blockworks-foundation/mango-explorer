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


# # 🥭 ConfidenceIntervalSpreadElement class
#
# Ignores any input `Order`s (so probably best at the head of the chain). Builds orders using a fixed position
# size ratio but with a spread based on the confidence in the oracle price.
#
class ConfidenceIntervalSpreadElement(Element):
    def __init__(self, position_size_ratio: Decimal, confidence_interval_levels: typing.Sequence[Decimal] = [Decimal(2)], order_type: mango.OrderType = mango.OrderType.POST_ONLY):
        super().__init__()
        self.position_size_ratio: Decimal = position_size_ratio
        self.confidence_interval_levels: typing.Sequence[Decimal] = confidence_interval_levels
        self.order_type: mango.OrderType = order_type

    def process(self, context: mango.Context, model_state: ModelState, orders: typing.Sequence[mango.Order]) -> typing.Sequence[mango.Order]:
        price: mango.Price = model_state.price
        if price.source.supports & mango.SupportedOracleFeature.CONFIDENCE == 0:
            raise Exception(f"Price does not support confidence interval: {price}")

        base_tokens: mango.TokenValue = model_state.inventory.base
        quote_tokens: mango.TokenValue = model_state.inventory.quote

        total = (base_tokens.value * price.mid_price) + quote_tokens.value
        quote_value_to_risk = total * self.position_size_ratio
        position_size = quote_value_to_risk / price.mid_price

        new_orders: typing.List[mango.Order] = []
        for confidence_interval_level in self.confidence_interval_levels:
            charge = price.confidence * confidence_interval_level
            bid: Decimal = price.mid_price - charge
            ask: Decimal = price.mid_price + charge

            new_orders += [
                mango.Order.from_basic_info(mango.Side.BUY, price=bid,
                                            quantity=position_size, order_type=self.order_type),
                mango.Order.from_basic_info(mango.Side.SELL, price=ask,
                                            quantity=position_size, order_type=self.order_type)
            ]

        new_orders.sort(key=lambda ord: ord.price, reverse=True)
        order_text = "\n    ".join([f"{order}" for order in new_orders])

        top_bid = model_state.top_bid
        top_ask = model_state.top_ask
        self.logger.debug(f"""Initial desired orders - spread {model_state.spread} ({top_bid.price if top_bid else None} / {top_ask.price if top_ask else None}):
    {order_text}""")
        return new_orders

    def __str__(self) -> str:
        return f"« 𝙲𝚘𝚗𝚏𝚒𝚍𝚎𝚗𝚌𝚎𝙸𝚗𝚝𝚎𝚛𝚟𝚊𝚕𝚂𝚙𝚛𝚎𝚊𝚍𝙴𝚕𝚎𝚖𝚎𝚗𝚝 {self.order_type} - position size: {self.position_size_ratio}, confidence interval levels: {self.confidence_interval_levels} »"
