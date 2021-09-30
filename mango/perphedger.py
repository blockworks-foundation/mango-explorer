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
import traceback

from decimal import Decimal
from solana.publickey import PublicKey

from .context import Context
from .orders import Side, OrderType, Order
from .marketoperations import MarketOperations
from .perpeventqueue import PerpFillEvent


# # 🥭 PerpHedger class
#
# A `PerpHedger` takes a `PerpFill` event and tries to hedge (apply the reverse trade) on the spot market.
#
class PerpHedger:
    def __init__(self, own_address: PublicKey, hedge_market_operations: MarketOperations, max_price_slippage_factor: Decimal):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.own_address: PublicKey = own_address
        self.hedge_market_operations: MarketOperations = hedge_market_operations
        self.buy_price_adjustment_factor: Decimal = Decimal("1") + max_price_slippage_factor
        self.sell_price_adjustment_factor: Decimal = Decimal("1") - max_price_slippage_factor
        self.hedging_on: str = self.hedge_market_operations.market.symbol

    def hedge(self, context: Context, fill_event: PerpFillEvent) -> Order:
        side: Side
        if fill_event.taker == self.own_address:
            opposite_side: Side = Side.BUY if fill_event.taker_side == Side.SELL else Side.SELL
            side = opposite_side
        else:
            # We were the opposite side in the filled trade, so to hedge we want to be the side the taker just took.
            side = fill_event.taker_side
        up_or_down: str = "up to" if side == Side.BUY else "down to"

        price_adjustment_factor: Decimal = self.sell_price_adjustment_factor if side == Side.SELL else self.buy_price_adjustment_factor
        adjusted_price: Decimal = fill_event.price * price_adjustment_factor
        quantity: Decimal = fill_event.quantity
        order: Order = Order.from_basic_info(side, adjusted_price, fill_event.quantity, OrderType.IOC)
        self.logger.info(
            f"Hedging perp {fill_event.taker_side} ({fill_event.maker_order_id}) of {fill_event.quantity:,.8f} at {fill_event.price:,.8f} with {side} of {quantity:,.8f} at {up_or_down} {adjusted_price:,.8f} on {self.hedging_on}\n\t{order}")
        try:
            self.hedge_market_operations.place_order(order)
        except Exception:
            self.logger.error(
                f"[{context.name}] Failed to hedge on {self.hedging_on} using order {order} - {traceback.format_exc()}")
        return order

    def __str__(self) -> str:
        return f"""« 𝙿𝚎𝚛𝚙𝙷𝚎𝚍𝚐𝚎𝚛 hedging on '{self.hedging_on}' [BUY * {self.buy_price_adjustment_factor} / SELL * {self.sell_price_adjustment_factor}] »"""

    def __repr__(self) -> str:
        return f"{self}"
