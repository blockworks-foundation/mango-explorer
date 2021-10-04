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

import enum
import logging
import typing

from decimal import Decimal

from mango.perpmarketinfo import PerpMarketInfo

from ..account import Account, AccountBasketBaseToken
from ..accounttokenvalues import AccountTokenValues, PricedAccountTokenValues
from ..cache import Cache, PerpMarketCache
from ..context import Context
from ..group import Group
from ..lotsizeconverter import NullLotSizeConverter
from ..openorders import OpenOrders
from ..perpaccount import PerpAccount
from ..spotmarketinfo import SpotMarketInfo
from ..token import Token
from ..tokenvalue import TokenValue


# # 🥭 HealthType enum
#
# Is the health calculation Initial or Maintenance?
#
class HealthType(enum.Enum):
    # We use strings here so that argparse can work with these as parameters.
    INITIAL = "INITIAL"
    MAINTENANCE = "MAINTENANCE"

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"{self}"


class HealthCalculator:
    def __init__(self, context: Context, health_type: HealthType):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.context: Context = context
        self.health_type: HealthType = health_type

    def _calculate_pessimistic_spot_value(self, values: PricedAccountTokenValues) -> typing.Tuple[TokenValue, TokenValue]:
        # base total if all bids were executed
        if_all_bids_executed: TokenValue = values.quote_token_locked + values.base_token_total

        # base total if all asks were executed
        if_all_asks_executed: TokenValue = values.base_token_free

        base: TokenValue
        quote: TokenValue
        if if_all_bids_executed > if_all_asks_executed:
            base = values.net_value + if_all_bids_executed
            quote = values.quote_token_free
            return base, quote
        else:
            base = values.net_value + if_all_asks_executed
            quote = values.base_token_locked + values.quote_token_total
            return base, quote

    def _calculate_pessimistic_perp_value(self, values: PricedAccountTokenValues) -> typing.Tuple[TokenValue, TokenValue]:
        return values.perp_base_position, values.perp_quote_position

    def _calculate_perp_value(self, basket_token: AccountBasketBaseToken, token_price: TokenValue, market_index: int, cache: Cache, unadjustment_factor: Decimal) -> typing.Tuple[Decimal, Decimal]:
        if basket_token.perp_account is None or basket_token.perp_account.empty:
            return Decimal(0), Decimal(0)

        perp_market_cache = cache.perp_market_cache[market_index]
        if perp_market_cache is None:
            raise Exception(f"Cache contains no perp market cache for market index {market_index}.")

        perp_account: PerpAccount = basket_token.perp_account
        token: Token = basket_token.token_info.token
        base_lot_size: Decimal = perp_account.lot_size_converter.base_lot_size
        quote_lot_size: Decimal = perp_account.lot_size_converter.quote_lot_size

        takerQuote: Decimal = perp_account.taker_quote * quote_lot_size
        base_position: Decimal = (perp_account.base_position + perp_account.taker_base) * base_lot_size
        bids_quantity: Decimal = perp_account.bids_quantity * base_lot_size
        asks_quantity: Decimal = perp_account.asks_quantity * base_lot_size
        if_all_bids_executed = token.shift_to_decimals(base_position + bids_quantity) * unadjustment_factor
        if_all_asks_executed = token.shift_to_decimals(base_position - asks_quantity) * unadjustment_factor

        if abs(if_all_bids_executed) > abs(if_all_asks_executed):
            quote_position = perp_account.quote_position - perp_account.unsettled_funding(perp_market_cache)
            full_quote_position = quote_position + takerQuote - (bids_quantity * token_price.value)
            return if_all_bids_executed, full_quote_position
        else:
            quote_position = perp_account.quote_position - perp_account.unsettled_funding(perp_market_cache)
            full_quote_position = quote_position + takerQuote + (asks_quantity * token_price.value)
            return if_all_asks_executed, full_quote_position

    def calculate(self, account: Account, open_orders_by_address: typing.Dict[str, OpenOrders], group: Group, cache: Cache) -> Decimal:
        priced_reports: typing.List[PricedAccountTokenValues] = []
        for asset in account.basket:
            # if (asset.deposit.value != 0) or (asset.borrow.value != 0) or (asset.net_value.value != 0):
            report: AccountTokenValues = AccountTokenValues.from_account_basket_base_token(
                asset, open_orders_by_address, group)
            price: TokenValue = group.token_price_from_cache(cache, report.base_token)
            perp_market_cache: typing.Optional[PerpMarketCache] = group.perp_market_cache_from_cache(
                cache, report.base_token)
            priced_report: PricedAccountTokenValues = report.priced(price, perp_market_cache)
            priced_reports += [priced_report]

        quote_token_free_in_open_orders: TokenValue = TokenValue(group.shared_quote_token.token, Decimal(0))
        quote_token_total_in_open_orders: TokenValue = TokenValue(group.shared_quote_token.token, Decimal(0))
        for priced_report in priced_reports:
            quote_token_free_in_open_orders += priced_report.quote_token_free
            quote_token_total_in_open_orders += priced_report.quote_token_total

        quote_report: AccountTokenValues = AccountTokenValues(account.shared_quote_token.token_info.token,
                                                              account.shared_quote_token.token_info.token,
                                                              account.shared_quote_token.deposit,
                                                              account.shared_quote_token.borrow,
                                                              TokenValue(group.shared_quote_token.token, Decimal(0)),
                                                              TokenValue(group.shared_quote_token.token, Decimal(0)),
                                                              quote_token_free_in_open_orders,
                                                              quote_token_total_in_open_orders,
                                                              TokenValue(group.shared_quote_token.token, Decimal(0)),
                                                              Decimal(0), Decimal(0), Decimal(0),
                                                              NullLotSizeConverter())

        health: Decimal = quote_report.net_value.value
        for priced_report in priced_reports:
            market_index = group.find_token_market_index(priced_report.base_token)
            spot_market: typing.Optional[SpotMarketInfo] = group.spot_markets[market_index]
            if spot_market is None:
                raise Exception(f"Could not find market for spot token {priced_report.base_token.symbol}.")

            base_value, quote_value = self._calculate_pessimistic_spot_value(priced_report)

            spot_weight = spot_market.init_asset_weight if base_value > 0 else spot_market.init_liab_weight
            spot_health = base_value.value * spot_weight

            perp_base, _ = self._calculate_pessimistic_perp_value(priced_report)
            perp_market: typing.Optional[PerpMarketInfo] = group.perp_markets[market_index]
            perp_health: Decimal = Decimal(0)
            if perp_market is not None:
                perp_weight = perp_market.init_asset_weight if perp_base > 0 else perp_market.init_liab_weight
                perp_health = perp_base.value * perp_weight

            health += spot_health
            health += perp_health
            health += quote_value.value
            health += priced_report.raw_perp_quote_position

        return health

    def __str__(self) -> str:
        return f"« 𝙷𝚎𝚊𝚕𝚝𝚑𝙲𝚊𝚕𝚌𝚞𝚕𝚊𝚝𝚘𝚛 [{self.health_type}] »"

    def __repr__(self) -> str:
        return f"{self}"
