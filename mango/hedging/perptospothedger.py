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

from decimal import Decimal

from .hedger import Hedger


# # 🥭 PerpToSpotHedger class
#
# A hedger that hedges perp positions using a spot market.
#
class PerpToSpotHedger(Hedger):
    def __init__(
        self,
        group: mango.Group,
        underlying_market: mango.PerpMarket,
        hedging_market: mango.SpotMarket,
        market_operations: mango.MarketOperations,
        max_price_slippage_factor: Decimal,
        max_hedge_chunk_quantity: Decimal,
        target_balance: mango.TargetBalance,
        action_threshold: Decimal,
        pause_threshold: int = 0,
    ) -> None:
        super().__init__()
        if (underlying_market.base != hedging_market.base) or (
            underlying_market.quote != hedging_market.quote
        ):
            raise Exception(
                f"Market {hedging_market.fully_qualified_symbol} cannot be used to hedge market {underlying_market.fully_qualified_symbol}."
            )

        if not mango.Instrument.symbols_match(
            target_balance.symbol, hedging_market.base.symbol
        ):
            raise Exception(
                f"Cannot target {target_balance.symbol} when hedging on {hedging_market.fully_qualified_symbol}"
            )

        self.underlying_market: mango.PerpMarket = underlying_market
        self.hedging_market: mango.SpotMarket = hedging_market
        self.market_operations: mango.MarketOperations = market_operations
        self.buy_price_adjustment_factor: Decimal = (
            Decimal("1") + max_price_slippage_factor
        )
        self.sell_price_adjustment_factor: Decimal = (
            Decimal("1") - max_price_slippage_factor
        )
        self.max_hedge_chunk_quantity: Decimal = max_hedge_chunk_quantity

        resolved_target: mango.InstrumentValue = target_balance.resolve(
            hedging_market.base, Decimal(0), Decimal(0)
        )
        self.target_balance: Decimal = (
            self.hedging_market.lot_size_converter.round_base(resolved_target.value)
        )
        self.action_threshold: Decimal = action_threshold

        self.market_index: int = group.slot_by_perp_market_address(
            underlying_market.address
        ).index

        self.pause_threshold: int = pause_threshold
        self.pause_counter: int = self.pause_threshold

    def pulse(self, context: mango.Context, model_state: mango.ModelState) -> None:
        if self.pause_counter < self.pause_threshold:
            self.pause_counter += 1
            self._logger.debug(
                f"Pausing trades for {self.pause_threshold} pulses - this is pulse {self.pause_counter}"
            )
            return

        try:
            perp_account: typing.Optional[
                mango.PerpAccount
            ] = model_state.account.perp_accounts_by_index[self.market_index]
            if perp_account is None:
                raise Exception(
                    f"Could not find perp account at index {self.market_index} in account {model_state.account.address}."
                )

            basket_token: typing.Optional[
                mango.AccountSlot
            ] = model_state.account.slots_by_index[self.market_index]
            if basket_token is None:
                raise Exception(
                    f"Could not find basket token at index {self.market_index} in account {model_state.account.address}."
                )

            token_balance: mango.InstrumentValue = basket_token.net_value
            perp_position: mango.InstrumentValue = perp_account.base_token_value

            # We're interested in maintaining the right size of hedge lots, so round everything to the hedge
            # market's lot size (even though perps have different lot sizes).
            perp_position_rounded: Decimal = (
                self.hedging_market.lot_size_converter.round_base(perp_position.value)
            )
            token_balance_rounded: Decimal = (
                self.hedging_market.lot_size_converter.round_base(token_balance.value)
            )

            # When we add the rounded perp position and token balances, we should get zero if we're delta-neutral.
            # If we have a target balance, subtract that to get our targetted delta neutral balance.
            delta: Decimal = (
                perp_position_rounded + token_balance_rounded - self.target_balance
            )
            self._logger.debug(
                f"Delta from {self.underlying_market.fully_qualified_symbol} to {self.hedging_market.fully_qualified_symbol} is {delta:,.8f} {basket_token.base_instrument.symbol}, action threshold is: {self.action_threshold}"
            )

            if delta.copy_abs() > self.action_threshold:
                side: mango.Side = mango.Side.BUY if delta < 0 else mango.Side.SELL
                up_or_down: str = "up to" if side == mango.Side.BUY else "down to"
                price_adjustment_factor: Decimal = (
                    self.sell_price_adjustment_factor
                    if side == mango.Side.SELL
                    else self.buy_price_adjustment_factor
                )

                adjusted_price: Decimal = (
                    model_state.price.mid_price * price_adjustment_factor
                )
                quantity: Decimal = delta.copy_abs()
                if (self.max_hedge_chunk_quantity > 0) and (
                    quantity > self.max_hedge_chunk_quantity
                ):
                    self._logger.debug(
                        f"Quantity to hedge ({quantity:,.8f}) is bigger than maximum quantity to hedge in one chunk {self.max_hedge_chunk_quantity:,.8f} - reducing quantity to {self.max_hedge_chunk_quantity:,.8f}."
                    )
                    quantity = self.max_hedge_chunk_quantity
                order: mango.Order = mango.Order.from_values(
                    side, adjusted_price, quantity, mango.OrderType.IOC
                )
                self._logger.info(
                    f"Hedging perp position {perp_position} and token balance {token_balance} with {side} of {quantity:,.8f} at {up_or_down} ({model_state.price}) {adjusted_price:,.8f} on {self.hedging_market.fully_qualified_symbol}\n\t{order}"
                )
                try:
                    self.market_operations.place_order(order)
                    self.pause_counter = 0
                except Exception:
                    self._logger.error(
                        f"[{context.name}] Failed to hedge on {self.hedging_market.fully_qualified_symbol} using order {order} - {traceback.format_exc()}"
                    )
                    raise

            self.pulse_complete.on_next(mango.local_now())
        except (
            mango.RateLimitException,
            mango.NodeIsBehindException,
            mango.BlockhashNotFoundException,
            mango.FailedToFetchBlockhashException,
        ) as common_exception:
            # Don't bother with a long traceback for these common problems.
            self._logger.error(
                f"[{context.name}] Hedger problem on pulse: {common_exception}"
            )
            self.pulse_error.on_next(common_exception)
        except Exception as exception:
            self._logger.error(
                f"[{context.name}] Hedger error on pulse:\n{traceback.format_exc()}"
            )
            self.pulse_error.on_next(exception)

    def __str__(self) -> str:
        return f"« PerpToSpotHedger for underlying '{self.underlying_market.fully_qualified_symbol}', hedging on '{self.hedging_market.fully_qualified_symbol}' »"
