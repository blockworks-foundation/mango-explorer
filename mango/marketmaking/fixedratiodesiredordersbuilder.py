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

from .desiredorder import DesiredOrder
from .desiredordersbuilder import DesiredOrdersBuilder
from .modelstate import ModelState


# # 🥭 FixedRatioDesiredOrdersBuilder class
#
# Builds orders using a fixed spread ratio and a fixed position size ratio.
#

class FixedRatioDesiredOrdersBuilder(DesiredOrdersBuilder):
    def __init__(self, spread_ratio: Decimal, position_size_ratio: Decimal):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.spread_ratio: Decimal = spread_ratio
        self.position_size_ratio: Decimal = position_size_ratio

    def build(self, context: mango.Context, model_state: ModelState) -> typing.Sequence[DesiredOrder]:
        price: mango.Price = model_state.price
        inventory: typing.Sequence[typing.Optional[mango.TokenValue]] = model_state.account.net_assets
        base_tokens: typing.Optional[mango.TokenValue] = mango.TokenValue.find_by_token(inventory, price.market.base)
        if base_tokens is None:
            raise Exception(f"Could not find market-maker base token {price.market.base.symbol} in inventory.")

        quote_tokens: typing.Optional[mango.TokenValue] = mango.TokenValue.find_by_token(inventory, price.market.quote)
        if quote_tokens is None:
            raise Exception(f"Could not find market-maker quote token {price.market.quote.symbol} in inventory.")

        total = (base_tokens.value * price.mid_price) + quote_tokens.value
        position_size = total * self.position_size_ratio

        buy_size: Decimal = position_size / price.mid_price
        sell_size: Decimal = position_size / price.mid_price

        bid: Decimal = price.mid_price - (price.mid_price * self.spread_ratio)
        ask: Decimal = price.mid_price + (price.mid_price * self.spread_ratio)

        return [
            DesiredOrder(mango.Side.BUY, mango.OrderType.POST_ONLY, bid, buy_size),
            DesiredOrder(mango.Side.SELL, mango.OrderType.POST_ONLY, ask, sell_size)
        ]

    def __str__(self) -> str:
        return f"« 𝙵𝚒𝚡𝚎𝚍𝚁𝚊𝚝𝚒𝚘𝙳𝚎𝚜𝚒𝚛𝚎𝚍𝙾𝚛𝚍𝚎𝚛𝚜𝙱𝚞𝚒𝚕𝚍𝚎𝚛 using ratios - spread: {self.spread_ratio}, position size: {self.position_size_ratio} »"
