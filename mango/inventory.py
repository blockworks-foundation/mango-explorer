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
import typing

from decimal import Decimal

from .account import Account
from .cache import Cache
from .calculators.collateralcalculator import CollateralCalculator
from .calculators.spotcollateralcalculator import SpotCollateralCalculator
from .calculators.perpcollateralcalculator import PerpCollateralCalculator
from .group import Group
from .market import InventorySource, Market
from .openorders import OpenOrders
from .perpmarket import PerpMarket
from .tokenvalue import TokenValue
from .watcher import Watcher


# # 🥭 Inventory class
#
# This class details inventory of a crypto account for a market.
#
class Inventory:
    def __init__(self, inventory_source: InventorySource, liquidity_incentives: TokenValue, available_collateral: TokenValue, base: TokenValue, quote: TokenValue):
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.inventory_source: InventorySource = inventory_source
        self.available_collateral: TokenValue = available_collateral
        self.liquidity_incentives: TokenValue = liquidity_incentives
        self.base: TokenValue = base
        self.quote: TokenValue = quote

    @property
    def symbol(self) -> str:
        return f"{self.base.token.symbol}/{self.quote.token.symbol}"

    def __str__(self) -> str:
        liquidity_incentives: str = ""
        if self.liquidity_incentives.value > 0:
            liquidity_incentives = f" {self.liquidity_incentives}"
        return f"« 𝙸𝚗𝚟𝚎𝚗𝚝𝚘𝚛𝚢 {self.symbol}{liquidity_incentives} [{self.base} / {self.quote}] ({self.available_collateral} available) »"

    def __repr__(self) -> str:
        return f"{self}"


class SpotInventoryAccountWatcher:
    def __init__(self, market: Market, account_watcher: Watcher[Account], group_watcher: Watcher[Group], all_open_orders_watchers: typing.Sequence[Watcher[OpenOrders]], cache_watcher: Watcher[Cache]):
        self.account_watcher: Watcher[Account] = account_watcher
        self.group_watcher: Watcher[Group] = group_watcher
        self.all_open_orders_watchers: typing.Sequence[Watcher[OpenOrders]] = all_open_orders_watchers
        self.cache_watcher: Watcher[Cache] = cache_watcher
        account: Account = account_watcher.latest
        base_value = TokenValue.find_by_symbol(account.net_assets, market.base.symbol)
        self.base_index: int = account.net_assets.index(base_value)
        quote_value = TokenValue.find_by_symbol(account.net_assets, market.quote.symbol)
        self.quote_index: int = account.net_assets.index(quote_value)
        self.collateral_calculator: CollateralCalculator = SpotCollateralCalculator()

    @property
    def latest(self) -> Inventory:
        account: Account = self.account_watcher.latest
        group: Group = self.group_watcher.latest
        cache: Cache = self.cache_watcher.latest

        # Spot markets don't accrue MNGO liquidity incentives
        mngo = group.find_token_info_by_symbol("MNGO").token
        mngo_accrued: TokenValue = TokenValue(mngo, Decimal(0))

        all_open_orders: typing.Dict[str, OpenOrders] = {
            str(oo_watcher.latest.address): oo_watcher.latest for oo_watcher in self.all_open_orders_watchers}
        available_collateral: TokenValue = self.collateral_calculator.calculate(account, all_open_orders, group, cache)

        base_value = account.net_assets[self.base_index]
        if base_value is None:
            raise Exception(
                f"Could not find net assets in account {account.address} at index {self.base_index}.")
        quote_value = account.net_assets[self.quote_index]
        if quote_value is None:
            raise Exception(
                f"Could not find net assets in account {account.address} at index {self.quote_index}.")

        return Inventory(InventorySource.ACCOUNT, mngo_accrued, available_collateral, base_value, quote_value)


class PerpInventoryAccountWatcher:
    def __init__(self, market: PerpMarket, account_watcher: Watcher[Account], group_watcher: Watcher[Group], cache_watcher: Watcher[Cache], group: Group):
        self.market: PerpMarket = market
        self.account_watcher: Watcher[Account] = account_watcher
        self.group_watcher: Watcher[Group] = group_watcher
        self.cache_watcher: Watcher[Cache] = cache_watcher
        self.perp_account_index: int = group.find_perp_market_index(market.address)
        account: Account = account_watcher.latest
        quote_value = TokenValue.find_by_symbol(account.net_assets, market.quote.symbol)
        self.quote_index: int = account.net_assets.index(quote_value)
        self.collateral_calculator: CollateralCalculator = PerpCollateralCalculator()

    @property
    def latest(self) -> Inventory:
        account: Account = self.account_watcher.latest
        group: Group = self.group_watcher.latest
        cache: Cache = self.cache_watcher.latest
        perp_account = account.perp_accounts[self.perp_account_index]
        if perp_account is None:
            raise Exception(
                f"Could not find perp account for {self.market.symbol} in account {account.address} at index {self.perp_account_index}.")

        available_collateral: TokenValue = self.collateral_calculator.calculate(account, {}, group, cache)

        base_lots = perp_account.base_position
        base_value = self.market.lot_size_converter.base_size_lots_to_number(base_lots)
        base_token_value = TokenValue(self.market.base, base_value)
        quote_token_value = account.net_assets[self.quote_index]
        if quote_token_value is None:
            raise Exception(f"Could not find net assets in account {account.address} at index {self.quote_index}.")
        return Inventory(InventorySource.ACCOUNT, perp_account.mngo_accrued, available_collateral, base_token_value, quote_token_value)
