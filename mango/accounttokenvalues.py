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

from decimal import Decimal

from .account import AccountBasketBaseToken
from .cache import PerpMarketCache
from .calculators.unsettledfundingcalculator import calculate_unsettled_funding, UnsettledFundingParams
from .group import Group
from .lotsizeconverter import LotSizeConverter
from .openorders import OpenOrders
from .perpaccount import PerpAccount
from .token import Token
from .tokenvalue import TokenValue


# # 🥭 _token_values_from_open_orders function
#
# `_token_values_from_open_orders()` builds TokenValue objects from an OpenOrders object.
#
def _token_values_from_open_orders(base_token: Token, quote_token: Token, spot_open_orders: typing.Sequence[OpenOrders]) -> typing.Tuple[TokenValue, TokenValue, TokenValue, TokenValue]:
    base_token_free: Decimal = Decimal(0)
    base_token_total: Decimal = Decimal(0)
    quote_token_free: Decimal = Decimal(0)
    quote_token_total: Decimal = Decimal(0)
    for open_orders in spot_open_orders:
        base_token_free += open_orders.base_token_free
        base_token_total += open_orders.base_token_total

        quote_token_free += open_orders.quote_token_free
        quote_token_total += open_orders.quote_token_total

    return (TokenValue(base_token, base_token_free),
            TokenValue(base_token, base_token_total),
            TokenValue(quote_token, quote_token_free),
            TokenValue(quote_token, quote_token_total))


# # 🥭 AccountTokenValues class
#
# `AccountTokenValues` gathers basket items together instead of separate arrays.
#
class AccountTokenValues:
    def __init__(self, base_token: Token, quote_token: Token, deposit: TokenValue, borrow: TokenValue, base_token_free: TokenValue, base_token_total: TokenValue, quote_token_free: TokenValue, quote_token_total: TokenValue, perp_base_position: TokenValue, raw_perp_quote_position: Decimal, long_settled_funding: Decimal, short_settled_funding: Decimal, lot_size_converter: LotSizeConverter):
        self.base_token: Token = base_token
        self.quote_token: Token = quote_token
        self.deposit: TokenValue = deposit
        self.borrow: TokenValue = borrow

        self.base_token_free: TokenValue = base_token_free
        self.base_token_total: TokenValue = base_token_total
        self.quote_token_free: TokenValue = quote_token_free
        self.quote_token_total: TokenValue = quote_token_total
        self.perp_base_position: TokenValue = perp_base_position
        self.raw_perp_quote_position: Decimal = raw_perp_quote_position
        self.long_settled_funding: Decimal = long_settled_funding
        self.short_settled_funding: Decimal = short_settled_funding
        self.lot_size_converter: LotSizeConverter = lot_size_converter

    @property
    def net_value(self) -> TokenValue:
        return self.deposit - self.borrow + self.base_token_total

    @property
    def base_token_locked(self) -> TokenValue:
        return self.base_token_total - self.base_token_free

    @property
    def quote_token_locked(self) -> TokenValue:
        return self.quote_token_total - self.quote_token_free

    def priced(self, price: TokenValue, perp_market_cache: typing.Optional[PerpMarketCache]) -> "PricedAccountTokenValues":
        return PricedAccountTokenValues(self, price, perp_market_cache)

    @staticmethod
    def from_account_basket_base_token(account_basket_token: AccountBasketBaseToken, open_orders_by_address: typing.Dict[str, OpenOrders], group: Group) -> "AccountTokenValues":
        base_token: Token = account_basket_token.token_info.token
        quote_token: Token = account_basket_token.quote_token_info.token
        perp_account: typing.Optional[PerpAccount] = account_basket_token.perp_account
        if perp_account is None:
            raise Exception(f"No perp account for basket token {account_basket_token.token_info.token.symbol}")

        open_orders: typing.Sequence[OpenOrders] = []
        if account_basket_token.spot_open_orders is not None:
            open_orders = [open_orders_by_address[str(account_basket_token.spot_open_orders)]]
        base_token_free, base_token_total, quote_token_free, quote_token_total = _token_values_from_open_orders(
            base_token, quote_token, open_orders)

        lot_size_converter: LotSizeConverter = perp_account.lot_size_converter
        perp_base_position: TokenValue = perp_account.base_token_value
        perp_quote_position: Decimal = perp_account.quote_position_raw
        long_settled_funding: Decimal = perp_account.long_settled_funding / lot_size_converter.quote_lot_size
        short_settled_funding: Decimal = perp_account.short_settled_funding / lot_size_converter.quote_lot_size

        return AccountTokenValues(base_token, quote_token, account_basket_token.deposit, account_basket_token.borrow, base_token_free, base_token_total, quote_token_free, quote_token_total, perp_base_position, perp_quote_position, long_settled_funding, short_settled_funding, lot_size_converter)

    def __str__(self) -> str:
        return f"""« 𝙰𝚌𝚌𝚘𝚞𝚗𝚝𝚃𝚘𝚔𝚎𝚗𝚁𝚎𝚙𝚘𝚛𝚝 {self.base_token.symbol}
    Deposited: {self.deposit}
    Borrowed : {self.borrow}
    Unsettled:
      Base   : {self.base_token_total} ({self.base_token_free} free)
      Quote  : {self.quote_token_total} ({self.quote_token_free} free)
    Net Value: {self.net_value}
»"""

    def __repr__(self) -> str:
        return f"{self}"


class PricedAccountTokenValues(AccountTokenValues):
    def __init__(self, original_account_token_values: AccountTokenValues, price: TokenValue, perp_market_cache: typing.Optional[PerpMarketCache]):
        deposit: TokenValue = original_account_token_values.deposit * price
        borrow: TokenValue = original_account_token_values.borrow * price
        base_token_free: TokenValue = original_account_token_values.base_token_free * price
        base_token_total: TokenValue = original_account_token_values.base_token_total * price

        perp_base_position: TokenValue = original_account_token_values.perp_base_position * price

        super().__init__(original_account_token_values.base_token, original_account_token_values.quote_token,
                         deposit, borrow, base_token_free, base_token_total,
                         original_account_token_values.quote_token_free,
                         original_account_token_values.quote_token_total,
                         perp_base_position, original_account_token_values.raw_perp_quote_position,
                         original_account_token_values.long_settled_funding, original_account_token_values.short_settled_funding,
                         original_account_token_values.lot_size_converter)
        self.original_account_token_values: AccountTokenValues = original_account_token_values
        self.price: TokenValue = price
        self.perp_market_cache: typing.Optional[PerpMarketCache] = perp_market_cache
        perp_quote_position: TokenValue = TokenValue(original_account_token_values.quote_token, Decimal(0))
        if perp_market_cache is not None:
            original: AccountTokenValues = original_account_token_values
            long_funding: Decimal = perp_market_cache.long_funding / original.lot_size_converter.quote_lot_size
            short_funding: Decimal = perp_market_cache.short_funding / original.lot_size_converter.quote_lot_size
            unsettled_funding: TokenValue = calculate_unsettled_funding(UnsettledFundingParams(
                quote_token=original.quote_token,
                base_position=original.perp_base_position,
                long_funding=long_funding,
                long_settled_funding=original.long_settled_funding,
                short_funding=short_funding,
                short_settled_funding=original.short_settled_funding
            ))
            perp_quote_position += unsettled_funding

        self.perp_quote_position: TokenValue = perp_quote_position

    def __str__(self) -> str:
        return f"""« 𝙿𝚛𝚒𝚌𝚎𝚍𝙰𝚌𝚌𝚘𝚞𝚗𝚝𝚃𝚘𝚔𝚎𝚗𝚅𝚊𝚕𝚞𝚎𝚜 {self.base_token.symbol} priced in {self.quote_token.symbol}
    Deposited: {self.original_account_token_values.deposit:<45} worth {self.deposit}
    Borrowed:  {self.original_account_token_values.borrow:<45} worth {self.borrow}
    Unsettled:
      Base   : {self.original_account_token_values.base_token_total:<45} worth {self.base_token_total}
      Quote  : {self.original_account_token_values.quote_token_total:<45} worth {self.quote_token_total}
    Perp:
      Base   : {self.original_account_token_values.perp_base_position:<45} worth {self.perp_base_position}
      Quote  : {self.perp_quote_position:<45} worth {self.perp_quote_position}
    Net Value: {self.original_account_token_values.net_value:<45} worth {self.net_value}
»"""

    def __repr__(self) -> str:
        return f"{self}"
