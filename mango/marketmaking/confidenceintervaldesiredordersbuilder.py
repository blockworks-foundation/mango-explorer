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

from decimal import Decimal

from .desiredordersbuilder import DesiredOrdersBuilder
from .modelstate import ModelState


# # 🥭 ConfidenceIntervalDesiredOrdersBuilder class
#
# Builds orders using a fixed position size ratio but with a spread based on the confidence in the oracle price.
#

class ConfidenceIntervalDesiredOrdersBuilder(DesiredOrdersBuilder):
    def __init__(self, position_size_ratio: Decimal, min_price_ratio: Decimal, max_price_ratio: Decimal, order_type: mango.OrderType = mango.OrderType.POST_ONLY):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.position_size_ratio: Decimal = position_size_ratio
        self.min_price_ratio: Decimal = min_price_ratio
        self.max_price_ratio: Decimal = max_price_ratio
        self.order_type: mango.OrderType = order_type

    def build(self, context: mango.Context, model_state: ModelState) -> typing.Sequence[mango.Order]:
        price: mango.Price = model_state.price
        if price.source.supports & mango.SupportedOracleFeature.CONFIDENCE == 0:
            raise Exception(f"Price does not support confidence interval: {price}")

        inventory: typing.Sequence[typing.Optional[mango.TokenValue]] = model_state.account.net_assets
        base_tokens: mango.TokenValue = mango.TokenValue.find_by_token(inventory, price.market.base)
        quote_tokens: mango.TokenValue = mango.TokenValue.find_by_token(inventory, price.market.quote)

        total = (base_tokens.value * price.mid_price) + quote_tokens.value
        position_size = total * self.position_size_ratio

        # From Daffy on 26th July 2021: max(pyth_conf * 2, price * min_charge)
        min_charge = max(price.confidence * 2, price.mid_price * self.min_price_ratio)
        charge = min(min_charge, price.mid_price * self.max_price_ratio)
        bid: Decimal = price.mid_price - charge
        ask: Decimal = price.mid_price + charge

        orders: typing.List[mango.Order] = [
            mango.Order.from_basic_info(mango.Side.BUY, price=bid,
                                        quantity=position_size, order_type=self.order_type),
            mango.Order.from_basic_info(mango.Side.SELL, price=ask,
                                        quantity=position_size, order_type=self.order_type)
        ]

        return orders

    def __str__(self) -> str:
        return f"« 𝙲𝚘𝚗𝚏𝚒𝚍𝚎𝚗𝚌𝚎𝙸𝚗𝚝𝚎𝚛𝚟𝚊𝚕𝙳𝚎𝚜𝚒𝚛𝚎𝚍𝙾𝚛𝚍𝚎𝚛𝚜𝙱𝚞𝚒𝚕𝚍𝚎𝚛 {self.order_type} - position size: {self.position_size_ratio}, min charge: {self.min_price_ratio}, max charge: {self.max_price_ratio} »"
