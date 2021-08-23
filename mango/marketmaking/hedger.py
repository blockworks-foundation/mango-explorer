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
import traceback
import rx

from decimal import Decimal


# # 🥭 Hedger class
#
# A `Hedger` watches for trades on one market and performs the opposite trade on a second market.
#
class Hedger(rx.core.typing.Disposable):
    def __init__(self, context: mango.Context, account: mango.Account, watched_market: mango.Market, hedge_market: mango.Market, initial: mango.PerpEventQueue, observable_event_queue: rx.Observable, operations: mango.MarketOperations, max_price_slippage_factor: Decimal):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.context: mango.Context = context
        self.account: mango.Account = account
        self.watched_market: mango.Market = watched_market
        self.hedge_market: mango.Market = hedge_market
        self.initial: mango.PerpEventQueue = initial
        self.observable_event_queue: rx.Observable = observable_event_queue

        self.splitter: mango.UnseenPerpEventChangesTracker = mango.UnseenPerpEventChangesTracker(initial)
        self.event_queue_subscription: rx.core.typing.Disposable = self.observable_event_queue.subscribe(
            on_next=self._trigger)
        self.buy_price_adjustment_factor: Decimal = Decimal("1") + max_price_slippage_factor
        self.sell_price_adjustment_factor: Decimal = Decimal("1") - max_price_slippage_factor
        self.operations: mango.MarketOperations = operations

    def _trigger(self, event_queue: mango.PerpEventQueue):
        try:
            unseen_events = self.splitter.unseen(event_queue)
            for unseen_event in unseen_events:
                if isinstance(unseen_event, mango.PerpFillEvent):
                    if (unseen_event.maker == self.account.address) or (unseen_event.taker == self.account.address):
                        if unseen_event.maker == unseen_event.taker:
                            self.logger.info(
                                f"Ignoring self-trade of {unseen_event.quantity:,.8f} at {unseen_event.price:,.8f} on {self.watched_market.symbol}.")
                        else:
                            self._hedge(unseen_event)
        except Exception:
            self.logger.error(
                f"[{self.context.name}] Error processing events from {self.watched_market.symbol} for hedging on {self.hedge_market.symbol} - {traceback.format_exc()}")

    def _hedge(self, event: mango.PerpFillEvent) -> None:
        opposite_side: mango.Side = mango.Side.BUY if event.side == mango.Side.SELL else mango.Side.SELL
        price_adjustment_factor: Decimal = self.sell_price_adjustment_factor if opposite_side == mango.Side.SELL else self.buy_price_adjustment_factor
        adjusted_price: Decimal = event.price * price_adjustment_factor
        quantity: Decimal = event.quantity
        order: mango.Order = mango.Order.from_basic_info(
            opposite_side, adjusted_price, event.quantity, mango.OrderType.IOC)
        up_or_down: str = "up to" if opposite_side == mango.Side.BUY else "down to"
        self.logger.info(
            f"Hedging {event.side} ({event.maker_order_id}) of {event.quantity:,.8f} at {event.price:,.8f} on {self.watched_market.symbol} with {opposite_side} of {quantity:,.8f} at {up_or_down} {adjusted_price:,.8f} on {self.hedge_market.symbol}\n\t{order}")
        try:
            self.operations.place_order(order)
        except Exception:
            self.logger.error(
                f"[{self.context.name}] Failed to hedge {self.watched_market.symbol} on {self.hedge_market.symbol} using order {order} - {traceback.format_exc()}")

    def dispose(self):
        self.event_queue_subscription.dispose()

    def __str__(self) -> str:
        return f"""« 𝙷𝚎𝚍𝚐𝚎𝚛 watching market '{self.watched_market.symbol}', hedging on '{self.hedge_market.symbol}'' »"""

    def __repr__(self) -> str:
        return f"{self}"
