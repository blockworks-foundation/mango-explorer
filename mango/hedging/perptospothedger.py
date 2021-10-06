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
import traceback
import typing

from datetime import datetime
from decimal import Decimal

from .hedger import Hedger


# # 🥭 PerpToSpotHedger class
#
# A hedger that hedges perp positions using a spot market.
#
class PerpToSpotHedger(Hedger):
    def __init__(self, group: mango.Group, underlying_market: mango.PerpMarket,
                 hedging_market: mango.SpotMarket, market_operations: mango.MarketOperations,
                 max_price_slippage_factor: Decimal, max_hedge_chunk_quantity: Decimal):
        super().__init__()
        if (underlying_market.base != hedging_market.base) or (underlying_market.quote != hedging_market.quote):
            raise Exception(
                f"Market {hedging_market.symbol} cannot be used to hedge market {underlying_market.symbol}.")

        self.underlying_market: mango.PerpMarket = underlying_market
        self.hedging_market: mango.SpotMarket = hedging_market
        self.market_operations: mango.MarketOperations = market_operations
        self.buy_price_adjustment_factor: Decimal = Decimal("1") + max_price_slippage_factor
        self.sell_price_adjustment_factor: Decimal = Decimal("1") - max_price_slippage_factor
        self.max_hedge_chunk_quantity: Decimal = max_hedge_chunk_quantity
        self.market_index: int = group.find_perp_market_index(underlying_market.address)

    def pulse(self, context: mango.Context, model_state: mango.ModelState):
        try:
            perp_account: typing.Optional[mango.PerpAccount] = model_state.account.perp_accounts[self.market_index]
            if perp_account is None:
                raise Exception(
                    f"Could not find perp account at index {self.market_index} in account {model_state.account.address}.")

            basket_token: typing.Optional[mango.AccountBasketToken] = model_state.account.basket_tokens[self.market_index]
            if basket_token is None:
                raise Exception(
                    f"Could not find basket token at index {self.market_index} in account {model_state.account.address}.")

            token_balance: mango.TokenValue = basket_token.net_value
            perp_position: mango.TokenValue = perp_account.base_token_value

            # We're interested in maintaining the right size of hedge lots, so round everything to the hedge
            # market's lot size (even though perps have different lot sizes).
            perp_position_rounded: Decimal = self.hedging_market.lot_size_converter.round_base(perp_position.value)
            token_balance_rounded: Decimal = self.hedging_market.lot_size_converter.round_base(token_balance.value)

            # When we add the rounded perp position and token balances, we should get zero if we're delta-neutral.
            delta: Decimal = perp_position_rounded + token_balance_rounded
            self.logger.debug(
                f"Delta from {self.underlying_market.symbol} to {self.hedging_market.symbol} is {delta:,.8f} {basket_token.token_info.token.symbol}")

            if delta != 0:
                side: mango.Side = mango.Side.BUY if delta < 0 else mango.Side.SELL
                up_or_down: str = "up to" if side == mango.Side.BUY else "down to"
                price_adjustment_factor: Decimal = self.sell_price_adjustment_factor if side == mango.Side.SELL else self.buy_price_adjustment_factor

                adjusted_price: Decimal = model_state.price.mid_price * price_adjustment_factor
                quantity: Decimal = abs(delta)
                if (self.max_hedge_chunk_quantity > 0) and (quantity > self.max_hedge_chunk_quantity):
                    self.logger.debug(
                        f"Quantity to hedge ({quantity:,.8f}) is bigger than maximum quantity to hedge in one chunk {self.max_hedge_chunk_quantity:,.8f} - reducing quantity to {self.max_hedge_chunk_quantity:,.8f}.")
                    quantity = self.max_hedge_chunk_quantity
                order: mango.Order = mango.Order.from_basic_info(side, adjusted_price, quantity, mango.OrderType.IOC)
                self.logger.info(
                    f"Hedging perp position {perp_position} and token balance {token_balance} with {side} of {quantity:,.8f} at {up_or_down} {adjusted_price:,.8f} on {self.hedging_market.symbol}\n\t{order}")
                try:
                    self.market_operations.place_order(order)
                except Exception:
                    self.logger.error(
                        f"[{context.name}] Failed to hedge on {self.hedging_market.symbol} using order {order} - {traceback.format_exc()}")
                    raise

            self.pulse_complete.on_next(datetime.now())
        except (mango.RateLimitException, mango.NodeIsBehindException, mango.BlockhashNotFoundException, mango.FailedToFetchBlockhashException) as common_exception:
            # Don't bother with a long traceback for these common problems.
            self.logger.error(f"[{context.name}] Hedger problem on pulse: {common_exception}")
            self.pulse_error.on_next(common_exception)
        except Exception as exception:
            self.logger.error(f"[{context.name}] Hedger error on pulse:\n{traceback.format_exc()}")
            self.pulse_error.on_next(exception)

    def __str__(self) -> str:
        return f"« 𝙿𝚎𝚛𝚙𝚃𝚘𝚂𝚙𝚘𝚝𝙷𝚎𝚍𝚐𝚎𝚛 for underlying '{self.underlying_market.symbol}', hedging on '{self.hedging_market.symbol}' »"
