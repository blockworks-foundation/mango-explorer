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


# # 🥭 FixedRatiosDesiredOrdersBuilder class
#
# Builds orders using a fixed spread ratio and a fixed position size ratio.
#

class FixedRatiosDesiredOrdersBuilder(DesiredOrdersBuilder):
    def __init__(self, spread_ratios: typing.Sequence[Decimal], position_size_ratios: typing.Sequence[Decimal], order_type: mango.OrderType = mango.OrderType.POST_ONLY):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        if len(spread_ratios) != len(position_size_ratios):
            raise Exception("List of spread ratios and position size ratios must be the same length.")

        self.spread_ratios: typing.Sequence[Decimal] = spread_ratios
        self.position_size_ratios: typing.Sequence[Decimal] = position_size_ratios
        self.order_type: mango.OrderType = order_type

    def build(self, context: mango.Context, model_state: ModelState) -> typing.Sequence[mango.Order]:
        price: mango.Price = model_state.price
        inventory: typing.Sequence[typing.Optional[mango.TokenValue]] = model_state.account.net_assets
        base_tokens: mango.TokenValue = mango.TokenValue.find_by_token(inventory, price.market.base)
        quote_tokens: mango.TokenValue = mango.TokenValue.find_by_token(inventory, price.market.quote)

        total = (base_tokens.value * price.mid_price) + quote_tokens.value

        orders: typing.List[mango.Order] = []
        for counter in range(len(self.spread_ratios)):
            position_size_ratio = self.position_size_ratios[counter]
            spread_ratio = self.spread_ratios[counter]

            position_size = total * position_size_ratio
            buy_quantity: Decimal = position_size / price.mid_price
            sell_quantity: Decimal = position_size / price.mid_price

            bid: Decimal = price.mid_price - (price.mid_price * spread_ratio)
            ask: Decimal = price.mid_price + (price.mid_price * spread_ratio)

            orders += [
                mango.Order.from_basic_info(mango.Side.BUY, price=bid,
                                            quantity=buy_quantity, order_type=self.order_type),
                mango.Order.from_basic_info(mango.Side.SELL, price=ask,
                                            quantity=sell_quantity, order_type=self.order_type)
            ]

        return orders

    def __str__(self) -> str:
        return f"« 𝙵𝚒𝚡𝚎𝚍𝚁𝚊𝚝𝚒𝚘𝙳𝚎𝚜𝚒𝚛𝚎𝚍𝙾𝚛𝚍𝚎𝚛𝚜𝙱𝚞𝚒𝚕𝚍𝚎𝚛 using ratios - spread: {self.spread_ratios}, position size: {self.position_size_ratios} »"
