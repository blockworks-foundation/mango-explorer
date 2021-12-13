# # ⚠ Warning
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
# LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN
# NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# [🥭 Mango Markets](https://markets/) support is available at:
#   [Docs](https://docs.markets/)
#   [Discord](https://discord.gg/67jySBhxrg)
#   [Twitter](https://twitter.com/mangomarkets)
#   [Github](https://github.com/blockworks-foundation)
#   [Email](mailto:hello@blockworks.foundation)

import typing

from datetime import datetime
from decimal import Decimal

from .account import AccountSlot
from .cache import PerpMarketCache, MarketCache, RootBankCache
from .calculators.unsettledfundingcalculator import calculate_unsettled_funding, UnsettledFundingParams
from .group import Group
from .instrumentvalue import InstrumentValue
from .lotsizeconverter import LotSizeConverter
from .openorders import OpenOrders
from .perpaccount import PerpAccount
from .token import Instrument, Token


# # 🥭 _token_values_from_open_orders function
#
# `_token_values_from_open_orders()` builds InstrumentValue objects from an OpenOrders object.
#
def _token_values_from_open_orders(base_token: Token, quote_token: Token, spot_open_orders: typing.Sequence[OpenOrders]) -> typing.Tuple[InstrumentValue, InstrumentValue, InstrumentValue, InstrumentValue]:
    base_token_free: Decimal = Decimal(0)
    base_token_total: Decimal = Decimal(0)
    quote_token_free: Decimal = Decimal(0)
    quote_token_total: Decimal = Decimal(0)
    for open_orders in spot_open_orders:
        base_token_free += open_orders.base_token_free
        base_token_total += open_orders.base_token_total

        quote_token_free += open_orders.quote_token_free
        quote_token_total += open_orders.quote_token_total

    return (InstrumentValue(base_token, base_token_free),
            InstrumentValue(base_token, base_token_total),
            InstrumentValue(quote_token, quote_token_free),
            InstrumentValue(quote_token, quote_token_total))


# # 🥭 AccountInstrumentValues class
#
# `AccountInstrumentValues` gathers basket items together instead of separate arrays.
#
class AccountInstrumentValues:
    def __init__(self, base_token: Instrument, quote_token: Token, raw_deposit: Decimal, deposit: InstrumentValue, raw_borrow: Decimal, borrow: InstrumentValue, base_token_free: InstrumentValue, base_token_total: InstrumentValue, quote_token_free: InstrumentValue, quote_token_total: InstrumentValue, perp_base_position: InstrumentValue, raw_perp_quote_position: Decimal, raw_taker_quote: Decimal, bids_quantity: InstrumentValue, asks_quantity: InstrumentValue, long_settled_funding: Decimal, short_settled_funding: Decimal, lot_size_converter: LotSizeConverter) -> None:
        self.base_token: Instrument = base_token
        self.quote_token: Token = quote_token
        self.raw_deposit: Decimal = raw_deposit
        self.deposit: InstrumentValue = deposit
        self.raw_borrow: Decimal = raw_borrow
        self.borrow: InstrumentValue = borrow

        self.base_token_free: InstrumentValue = base_token_free
        self.base_token_total: InstrumentValue = base_token_total
        self.quote_token_free: InstrumentValue = quote_token_free
        self.quote_token_total: InstrumentValue = quote_token_total
        self.perp_base_position: InstrumentValue = perp_base_position
        self.raw_perp_quote_position: Decimal = raw_perp_quote_position
        self.raw_taker_quote: Decimal = raw_taker_quote
        self.bids_quantity: InstrumentValue = bids_quantity
        self.asks_quantity: InstrumentValue = asks_quantity
        self.long_settled_funding: Decimal = long_settled_funding
        self.short_settled_funding: Decimal = short_settled_funding
        self.lot_size_converter: LotSizeConverter = lot_size_converter

    @property
    def net_value(self) -> InstrumentValue:
        return self.deposit - self.borrow + self.base_token_total

    @property
    def base_token_locked(self) -> InstrumentValue:
        return self.base_token_total - self.base_token_free

    @property
    def quote_token_locked(self) -> InstrumentValue:
        return self.quote_token_total - self.quote_token_free

    @property
    def if_all_bids_executed(self) -> InstrumentValue:
        return self.perp_base_position + self.bids_quantity

    @property
    def if_all_asks_executed(self) -> InstrumentValue:
        return self.perp_base_position - self.asks_quantity

    def priced(self, market_cache: MarketCache) -> "PricedAccountInstrumentValues":
        # We can only price actual SPL tokens
        if isinstance(self.base_token, Token):
            return PricedAccountInstrumentValues(self, market_cache)
        null_root_bank = RootBankCache(Decimal(1), Decimal(1), datetime.now())
        market_cache_with_null_root_bank = MarketCache(market_cache.price, null_root_bank, market_cache.perp_market)
        return PricedAccountInstrumentValues(self, market_cache_with_null_root_bank)

    @staticmethod
    def from_account_basket_base_token(account_slot: AccountSlot, open_orders_by_address: typing.Dict[str, OpenOrders], group: Group) -> "AccountInstrumentValues":
        base_token: Instrument = account_slot.base_instrument
        quote_token: Token = Token.ensure(account_slot.quote_token_bank.token)
        perp_account: typing.Optional[PerpAccount] = account_slot.perp_account
        if perp_account is None:
            raise Exception(f"No perp account for basket token {account_slot.base_instrument.symbol}")

        base_token_free: InstrumentValue = InstrumentValue(base_token, Decimal(0))
        base_token_total: InstrumentValue = InstrumentValue(base_token, Decimal(0))
        quote_token_free: InstrumentValue = InstrumentValue(quote_token, Decimal(0))
        quote_token_total: InstrumentValue = InstrumentValue(quote_token, Decimal(0))
        if account_slot.spot_open_orders is not None:
            open_orders: typing.Sequence[OpenOrders] = [
                open_orders_by_address[str(account_slot.spot_open_orders)]]
            base_token_free, base_token_total, quote_token_free, quote_token_total = _token_values_from_open_orders(
                Token.ensure(base_token), Token.ensure(quote_token), open_orders)

        lot_size_converter: LotSizeConverter = perp_account.lot_size_converter
        perp_base_position: InstrumentValue = perp_account.base_token_value
        perp_quote_position: Decimal = perp_account.quote_position_raw
        long_settled_funding: Decimal = perp_account.long_settled_funding / lot_size_converter.quote_lot_size
        short_settled_funding: Decimal = perp_account.short_settled_funding / lot_size_converter.quote_lot_size

        taker_quote: Decimal = perp_account.taker_quote * lot_size_converter.quote_lot_size
        bids_quantity: InstrumentValue = InstrumentValue(base_token, base_token.shift_to_decimals(
            perp_account.bids_quantity * lot_size_converter.base_lot_size))
        asks_quantity: InstrumentValue = InstrumentValue(base_token, base_token.shift_to_decimals(
            perp_account.asks_quantity * lot_size_converter.base_lot_size))

        return AccountInstrumentValues(base_token, quote_token, account_slot.raw_deposit, account_slot.deposit, account_slot.raw_borrow, account_slot.borrow, base_token_free, base_token_total, quote_token_free, quote_token_total, perp_base_position, perp_quote_position, taker_quote, bids_quantity, asks_quantity, long_settled_funding, short_settled_funding, lot_size_converter)

    def __str__(self) -> str:
        return f"""« AccountInstrumentValues {self.base_token.symbol}
    Deposited  : {self.deposit}
    Borrowed   : {self.borrow}
    Unsettled:
      Base     : {self.base_token_total} ({self.base_token_free} free)
      Quote    : {self.quote_token_total} ({self.quote_token_free} free)
    Perp:
      Base     : {self.perp_base_position}
      Quote    : {self.raw_perp_quote_position}
    If Executed:
      All Bids : {self.if_all_bids_executed}
      All Asks : {self.if_all_asks_executed}
    Net Value  : {self.net_value}
»"""

    def __repr__(self) -> str:
        return f"{self}"


class PricedAccountInstrumentValues(AccountInstrumentValues):
    def __init__(self, original_account_token_values: AccountInstrumentValues, market_cache: MarketCache) -> None:
        price: InstrumentValue = market_cache.adjusted_price(
            original_account_token_values.base_token, original_account_token_values.quote_token)

        if market_cache.root_bank is None:
            raise Exception(f"No root bank for token {original_account_token_values.base_token} in {market_cache}")

        deposit_value: Decimal = original_account_token_values.raw_deposit * market_cache.root_bank.deposit_index * price.value
        shifted_deposit_value: Decimal = original_account_token_values.quote_token.shift_to_decimals(deposit_value)
        deposit: InstrumentValue = InstrumentValue(original_account_token_values.quote_token, shifted_deposit_value)

        borrow_value: Decimal = original_account_token_values.raw_borrow * market_cache.root_bank.borrow_index * price.value
        shifted_borrow_value: Decimal = original_account_token_values.quote_token.shift_to_decimals(borrow_value)
        borrow: InstrumentValue = InstrumentValue(original_account_token_values.quote_token, shifted_borrow_value)

        base_token_free: InstrumentValue = original_account_token_values.base_token_free * price
        base_token_total: InstrumentValue = original_account_token_values.base_token_total * price

        perp_base_position: InstrumentValue = original_account_token_values.perp_base_position * price

        super().__init__(original_account_token_values.base_token, original_account_token_values.quote_token,
                         original_account_token_values.raw_deposit, deposit,
                         original_account_token_values.raw_borrow, borrow, base_token_free, base_token_total,
                         original_account_token_values.quote_token_free,
                         original_account_token_values.quote_token_total,
                         perp_base_position, original_account_token_values.raw_perp_quote_position,
                         original_account_token_values.raw_taker_quote,
                         original_account_token_values.bids_quantity, original_account_token_values.asks_quantity,
                         original_account_token_values.long_settled_funding, original_account_token_values.short_settled_funding,
                         original_account_token_values.lot_size_converter)
        self.original_account_token_values: AccountInstrumentValues = original_account_token_values
        self.price: InstrumentValue = price
        self.perp_market_cache: typing.Optional[PerpMarketCache] = market_cache.perp_market
        perp_quote_position: InstrumentValue = InstrumentValue(
            original_account_token_values.quote_token, original_account_token_values.raw_perp_quote_position)
        if market_cache.perp_market is not None:
            original: AccountInstrumentValues = original_account_token_values
            long_funding: Decimal = market_cache.perp_market.long_funding / original.lot_size_converter.quote_lot_size
            short_funding: Decimal = market_cache.perp_market.short_funding / original.lot_size_converter.quote_lot_size
            unsettled_funding: InstrumentValue = calculate_unsettled_funding(UnsettledFundingParams(
                quote_token=original.quote_token,
                base_position=original.perp_base_position,
                long_funding=long_funding,
                long_settled_funding=original.long_settled_funding,
                short_funding=short_funding,
                short_settled_funding=original.short_settled_funding
            ))
            perp_quote_position -= unsettled_funding

        self.perp_quote_position: InstrumentValue = perp_quote_position

    @property
    def if_all_bids_executed(self) -> InstrumentValue:
        return self.perp_base_position + (self.bids_quantity * self.price)

    @property
    def if_all_asks_executed(self) -> InstrumentValue:
        return self.perp_base_position - (self.asks_quantity * self.price)

    def if_worst_execution(self) -> typing.Tuple[InstrumentValue, InstrumentValue]:
        taker_quote: InstrumentValue = InstrumentValue(self.perp_quote_position.token, self.raw_taker_quote)
        # print("Quote calc", self.perp_quote_position, taker_quote, self.bids_quantity, self.price)

        if abs(self.if_all_bids_executed.value) > abs(self.if_all_asks_executed.value):
            base_position = self.if_all_bids_executed
            quote_position = self.perp_quote_position + taker_quote - (self.bids_quantity * self.price)
        else:
            base_position = self.if_all_asks_executed
            quote_position = self.perp_quote_position + taker_quote + (self.asks_quantity * self.price)

        return base_position, quote_position

    def __str__(self) -> str:
        return f"""« PricedAccountInstrumentValues {self.base_token.symbol} priced in {self.quote_token.symbol}
    Deposited  : {self.original_account_token_values.deposit:<45} worth {self.deposit}
    Borrowed   : {self.original_account_token_values.borrow:<45} worth {self.borrow}
    Unsettled:
      Base     : {self.original_account_token_values.base_token_total:<45} worth {self.base_token_total}
      Quote    : {self.original_account_token_values.quote_token_total:<45} worth {self.quote_token_total}
    Perp:
      Base     : {self.original_account_token_values.perp_base_position:<45} worth {self.perp_base_position}
      Quote    : {self.perp_quote_position:<45} worth {self.perp_quote_position}
    If Executed:
      All Bids : {self.original_account_token_values.if_all_bids_executed:<45} worth {self.if_all_bids_executed}
      All Asks : {self.original_account_token_values.if_all_asks_executed:<45} worth {self.if_all_asks_executed}
    Net Value  : {self.original_account_token_values.net_value:<45} worth {self.net_value}
»"""

    def __repr__(self) -> str:
        return f"{self}"
