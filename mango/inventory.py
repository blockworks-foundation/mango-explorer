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
from .group import Group
from .instrumentvalue import InstrumentValue
from .loadedmarket import LoadedMarket
from .markets import InventorySource
from .openorders import OpenOrders
from .perpmarket import PerpMarket
from .spotmarket import SpotMarket
from .watcher import Watcher


# # 🥭 Inventory class
#
# This class details inventory of a crypto account for a market.
#
class Inventory:
    def __init__(
        self,
        inventory_source: InventorySource,
        liquidity_incentives: InstrumentValue,
        available_collateral: InstrumentValue,
        base: InstrumentValue,
        quote: InstrumentValue,
    ) -> None:
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.inventory_source: InventorySource = inventory_source
        self.available_collateral: InstrumentValue = available_collateral
        self.liquidity_incentives: InstrumentValue = liquidity_incentives
        self.base: InstrumentValue = base
        self.quote: InstrumentValue = quote

    @property
    def symbol(self) -> str:
        return f"{self.base.token.symbol}/{self.quote.token.symbol}"

    def __str__(self) -> str:
        liquidity_incentives: str = ""
        if self.liquidity_incentives.value > 0:
            liquidity_incentives = f" {self.liquidity_incentives}"
        return f"« Inventory {self.symbol}{liquidity_incentives} [{self.base} / {self.quote}] ({self.available_collateral} available) »"

    def __repr__(self) -> str:
        return f"{self}"


class InventoryAccountWatcher:
    def __init__(
        self,
        market: LoadedMarket,
        account_watcher: Watcher[Account],
        group_watcher: Watcher[Group],
        all_open_orders_watchers: typing.Sequence[Watcher[OpenOrders]],
        cache_watcher: Watcher[Cache],
    ):
        self.account_watcher: Watcher[Account] = account_watcher
        self.group_watcher: Watcher[Group] = group_watcher
        self.all_open_orders_watchers: typing.Sequence[
            Watcher[OpenOrders]
        ] = all_open_orders_watchers
        self.cache_watcher: Watcher[Cache] = cache_watcher
        account: Account = account_watcher.latest
        if SpotMarket.isa(market):
            self.spot_account_index: int = (
                group_watcher.latest.slot_by_spot_market_address(market.address).index
            )
        elif PerpMarket.isa(market):
            self.spot_account_index = group_watcher.latest.slot_by_perp_market_address(
                market.address
            ).index
        else:
            raise Exception(
                f"Cannot find slot for market {market} in group {group_watcher.latest.address}"
            )

        base_value = InstrumentValue.find_by_symbol(
            account.net_values, market.base.symbol
        )
        self.base_index: int = account.net_values_by_index.index(base_value)
        quote_value = InstrumentValue.find_by_symbol(
            account.net_values, market.quote.symbol
        )
        self.quote_index: int = account.net_values_by_index.index(quote_value)

    @property
    def latest(self) -> Inventory:
        account: Account = self.account_watcher.latest
        group: Group = self.group_watcher.latest
        cache: Cache = self.cache_watcher.latest

        # Spot markets don't accrue MNGO liquidity incentives
        mngo = group.liquidity_incentive_token
        mngo_accrued: InstrumentValue = InstrumentValue(mngo, Decimal(0))

        all_open_orders: typing.Dict[str, OpenOrders] = {
            str(oo_watcher.latest.address): oo_watcher.latest
            for oo_watcher in self.all_open_orders_watchers
        }

        frame = account.to_dataframe(group, all_open_orders, cache)
        available_collateral: InstrumentValue = account.init_health(frame)

        base_value = account.net_values_by_index[self.base_index]
        if base_value is None:
            raise Exception(
                f"Could not find net assets in account {account.address} at index {self.base_index}."
            )
        quote_value = account.net_values_by_index[self.quote_index]
        if quote_value is None:
            raise Exception(
                f"Could not find net assets in account {account.address} at index {self.quote_index}."
            )

        return Inventory(
            InventorySource.ACCOUNT,
            mngo_accrued,
            available_collateral,
            base_value,
            quote_value,
        )
